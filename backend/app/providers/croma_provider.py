import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import settings
from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.providers.base import BaseProductProvider
from app.services.normalization_service import NormalizationService

logger = logging.getLogger(__name__)

ELECTRONIC_CATEGORIES = {
    "laptop", "phone", "tv", "headphones", "camera", "smartwatch",
    "washing_machine", "monitor", "keyboard", "general"
}


def _clean_number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, dict):
        value = value.get("amount") or value.get("value") or value.get("price")
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"\d[\d,]*(?:\.\d+)?", value)
    return float(match.group(0).replace(",", "")) if match else None


class CromaProvider(BaseProductProvider):
    """
    Croma Electronics Store Provider.
    Discovers authentic electronic gadgets on Croma India with live prices in INR,
    direct product links, star ratings, and verified buyer review counts.
    """

    def __init__(self):
        super().__init__(
            provider_id="croma_electronics",
            name="Croma Electronics Store",
            marketplace="Croma"
        )
        self.endpoint = "https://serpapi.com/search"

    def is_configured(self) -> bool:
        if not settings.ENABLE_CROMA_PROVIDER:
            return False
        key = (settings.SERPAPI_KEY or "").strip()
        return bool(key) and not key.upper().startswith(("YOUR_", "REPLACE_", "<"))

    def is_enabled(self) -> bool:
        return settings.ENABLE_CROMA_PROVIDER

    def get_required_env_keys(self) -> List[str]:
        return ["SERPAPI_KEY"] if not self.is_configured() else []

    @classmethod
    def normalize_croma_record(
        cls,
        title: str,
        product_url: str,
        category: str,
        current_price: Optional[float] = None,
        original_price: Optional[float] = None,
        rating: Optional[float] = None,
        review_count: Optional[int] = None,
        image_url: str = "",
        brand: str = "",
        availability: str = "In Stock",
        raw_data: Optional[Dict[str, Any]] = None
    ) -> Optional[NormalizedProduct]:
        clean_url = NormalizationService.unwrap_product_url(product_url)
        if not clean_url or not title:
            return None

        # Ensure product URL is a direct Croma product link
        if not NormalizationService.is_direct_product_url(clean_url, "Croma"):
            return None

        # Clean prices
        discount = None
        if original_price and current_price and original_price > current_price > 0:
            discount = round(((original_price - current_price) / original_price) * 100, 1)

        # Extract brand if missing
        if not brand or brand.lower() in ("unknown", "generic", "croma"):
            first_word = title.strip().split()[0]
            brand = first_word if len(first_word) > 2 else "Croma"

        # Unique stable ID
        match_id = re.search(r"/p/(\d+)", clean_url)
        croma_id = match_id.group(1) if match_id else str(abs(hash(clean_url)))

        product = NormalizedProduct(
            id=f"croma_{croma_id}",
            source_product_id=croma_id,
            title=title.strip(),
            brand=brand,
            category=category,
            image_url=image_url,
            current_price=current_price,
            original_price=original_price,
            discount_percent=discount,
            currency="INR",
            rating=rating,
            review_count=review_count,
            availability=availability or "In Stock",
            product_url=clean_url,
            marketplace="Croma",
            provider="croma_electronics",
            seller="Croma Official Retail",
            source="Croma Electronics India",
            specifications={"Marketplace": "Croma", "Store": "Croma Official Online Store"},
            features=[f"Available at Croma in INR"] + ([f"Rating: {rating:.1f}/5"] if rating else []),
            raw_data=raw_data or {},
            offers=[
                MarketplaceOffer(
                    marketplace="Croma",
                    provider="croma_electronics",
                    product_url=clean_url,
                    current_price=current_price,
                    original_price=original_price,
                    discount_percent=discount,
                    currency="INR",
                    in_stock=True if availability == "In Stock" else None,
                    rating=rating,
                    review_count=review_count,
                    seller_name="Croma"
                )
            ]
        )
        return NormalizationService.normalize_product(product)

    async def _search_serpapi(self, query: str, category: str, limit: int) -> List[NormalizedProduct]:
        """Fetch Croma products via SerpApi Google Shopping engine."""
        if not settings.SERPAPI_KEY:
            return []

        params = {
            "engine": "google_shopping",
            "q": f"{query} Croma",
            "location": "India",
            "gl": "in",
            "hl": "en",
            "api_key": settings.SERPAPI_KEY,
            "num": min(limit, 15)
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.endpoint, params=params)
            if resp.status_code != 200:
                logger.warning("SerpApi Croma query returned HTTP %d", resp.status_code)
                return []

            data = resp.json()
            shopping_results = data.get("shopping_results", [])
            products: List[NormalizedProduct] = []

            for item in shopping_results:
                source = item.get("source", "")
                link = item.get("link", "") or item.get("product_link", "")

                # Only include Croma products
                if "croma" not in source.lower() and "croma.com" not in link.lower():
                    continue

                title = item.get("title", "")
                current_price = _clean_number(item.get("extracted_price", item.get("price")))
                original_price = _clean_number(item.get("extracted_old_price", item.get("old_price")))
                rating = float(item.get("rating")) if item.get("rating") else None
                reviews = int(item.get("reviews")) if item.get("reviews") else None
                image_url = item.get("thumbnail", "")

                prod = self.normalize_croma_record(
                    title=title,
                    product_url=link,
                    category=category,
                    current_price=current_price,
                    original_price=original_price,
                    rating=rating,
                    review_count=reviews,
                    image_url=image_url,
                    brand=item.get("brand", ""),
                    raw_data=item
                )
                if prod:
                    products.append(prod)
                    if len(products) >= limit:
                        break

            return products

    async def _search_live_web(self, query: str, category: str, limit: int) -> List[NormalizedProduct]:
        """Discover live authentic Croma product pages using public search indexes."""
        search_terms = f"site:croma.com/p {query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 not installed; live Croma search fallback disabled")
            return []

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": search_terms},
                headers=headers
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("div", class_="result")
            products: List[NormalizedProduct] = []

            for res in results[:limit * 2]:
                title_tag = res.find("a", class_="result__a")
                snippet_tag = res.find("a", class_="result__snippet")
                if not title_tag:
                    continue

                raw_title = title_tag.get_text().strip()
                raw_href = title_tag.get("href", "")
                snippet = snippet_tag.get_text().strip() if snippet_tag else ""

                # Unpack redirect URL
                parsed = parse_qs(urlparse(raw_href).query)
                direct_url = parsed.get("uddg", [raw_href])[0]

                if "croma.com" not in direct_url.lower() or "/p/" not in direct_url.lower():
                    continue

                # Clean Title (strip " | Croma" or "... - Croma")
                clean_title = re.sub(r"\s*[-|]\s*Croma.*$", "", raw_title, flags=re.IGNORECASE).strip()

                # Extract price if present in snippet (e.g. ₹64,990 or Rs. 64,990)
                price_match = re.search(r"(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d+)?)", f"{clean_title} {snippet}", re.IGNORECASE)
                current_price = _clean_number(price_match.group(1)) if price_match else None

                # Extract rating if present in snippet (e.g. "4.3 out of 5" or "4.3 ★")
                rating = None
                rating_match = re.search(r"(\d\.\d)\s*(?:out of 5|stars|★|\/5)", f"{clean_title} {snippet}", re.IGNORECASE)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except ValueError:
                        rating = None

                # Extract review count
                review_count = None
                reviews_match = re.search(r"([\d,]+)\s*(?:reviews|ratings|buyer ratings)", f"{clean_title} {snippet}", re.IGNORECASE)
                if reviews_match:
                    try:
                        review_count = int(reviews_match.group(1).replace(",", ""))
                    except ValueError:
                        review_count = None

                prod = self.normalize_croma_record(
                    title=clean_title,
                    product_url=direct_url,
                    category=category,
                    current_price=current_price,
                    rating=rating,
                    review_count=review_count,
                    raw_data={"source": "croma_live_web", "snippet": snippet}
                )
                if prod:
                    products.append(prod)
                    if len(products) >= limit:
                        break

            return products

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()

        # Only run for electronic categories
        if category not in ELECTRONIC_CATEGORIES:
            self._last_status = "idle"
            self._last_message = f"Skipped for non-electronics category '{category}'"
            self._last_items_count = 0
            return []

        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "SERPAPI_KEY is required for the Croma SerpApi integration."
            self._last_items_count = 0
            self._last_latency_ms = (time.time() - start_time) * 1000
            return []

        products: List[NormalizedProduct] = []

        # 1. Try SerpApi if key is configured
        try:
            products = await self._search_serpapi(query, category, limit)
        except Exception as e:
            logger.warning("SerpApi Croma search failed: %s", e)

        self._last_latency_ms = (time.time() - start_time) * 1000
        self._last_items_count = len(products)

        if products:
            self._last_status = "active"
            self._last_message = f"Fetched {len(products)} live Croma electronics products."
        else:
            self._last_status = "empty"
            self._last_message = "No live Croma products found matching this query."

        return products
