"""Live Amazon and Flipkart product discovery through Bright Data."""

import asyncio
import logging
import os
import re
import time
from typing import Any, List, Optional

from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.providers.base import BaseProductProvider

logger = logging.getLogger(__name__)
from app.services.brightdata_service import (
    BrightDataServiceError,
    fetch_amazon_reviews,
    fetch_flipkart_products,
    search_amazon,
    search_flipkart_product_urls,
    search_flipkart_records,
)
from app.services.normalization_service import NormalizationService


def _number(value: Any) -> Optional[float]:
    """Parse Bright Data numeric fields whether they are numbers or formatted strings."""
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


class BrightDataAmazonProvider(BaseProductProvider):
    def __init__(self):
        super().__init__(
            provider_id="brightdata_amazon_search",
            name="Bright Data Amazon Search",
            marketplace="Amazon India",
        )

    def is_configured(self) -> bool:
        key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
        return bool(key) and not key.startswith("YOUR_")

    def get_required_env_keys(self) -> List[str]:
        return ["BRIGHTDATA_API_KEY"]

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        started = time.time()
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "Bright Data API key required in BRIGHTDATA_API_KEY."
            self._last_items_count = 0
            return []

        try:
            records = await asyncio.to_thread(search_amazon, query)
            products: List[NormalizedProduct] = []
            for record in records[:limit]:
                title = record.get("title") or record.get("name") or record.get("product_name")
                product_url = record.get("product_url") or record.get("url")
                asin = record.get("asin") or record.get("source_product_id")
                if not product_url and asin:
                    asin_clean = str(asin).strip().upper()
                    if re.match(r'^[A-Z0-9]{10}$', asin_clean):
                        product_url = f"https://www.amazon.in/dp/{asin_clean}"
                if not title or not product_url:
                    continue

                current_price, original_price, discount = NormalizationService.extract_product_prices(record)
                image_candidates = record.get("image_candidates") or []
                if not image_candidates:
                    image_candidates = NormalizationService.extract_image_candidates(
                        record,
                        [
                            "image_url", "image", "main_image", "primary_image", "thumbnail",
                            "image_link", "image_urls", "additional_image_urls", "images",
                            "additional_images", "product_images"
                        ]
                    )
                image_url = record.get("image_url") or (image_candidates[0] if image_candidates else "")
                product = NormalizedProduct(
                    id=f"brightdata_{asin or product_url}",
                    source_product_id=str(asin) if asin else None,
                    title=title,
                    brand=record.get("brand") or "Unknown",
                    category=category,
                    image_url=image_url,
                    image_candidates=image_candidates,
                    current_price=current_price,
                    original_price=original_price,
                    discount_percent=record.get("discount") or None,
                    currency="INR",
                    rating=_number(record.get("rating")),
                    review_count=_number(record.get("review_count", record.get("reviews_count", record.get("num_ratings")))),
                    availability=record.get("availability") or "Unknown",
                    product_url=product_url,
                    marketplace="Amazon India",
                    provider=self.provider_id,
                    seller=record.get("seller"),
                    source="Bright Data Amazon Products Search",
                    specifications={"ASIN": str(asin)} if asin else {},
                    features=record.get("features") or [],
                    raw_data=record,
                    offers=[MarketplaceOffer(
                        marketplace="Amazon India",
                        provider=self.provider_id,
                        product_url=product_url,
                        current_price=current_price,
                        original_price=original_price,
                        discount_percent=record.get("discount") or None,
                        currency="INR",
                        rating=_number(record.get("rating")),
                        review_count=_number(record.get("review_count", record.get("reviews_count", record.get("num_ratings")))),
                        seller_name=record.get("seller"),
                    )],
                )
                products.append(NormalizationService.normalize_product(product))

            # Enrich top candidate products with authentic customer review text from Bright Data
            urls_to_enrich = [p.product_url for p in products[:3] if p.product_url]
            if urls_to_enrich:
                try:
                    review_map = await asyncio.to_thread(fetch_amazon_reviews, urls_to_enrich)
                    for p in products:
                        asin = p.source_product_id or p.specifications.get("ASIN")
                        entry = review_map.get(asin) or review_map.get(p.product_url) or {}
                        revs = entry.get("reviews") or []
                        if revs:
                            p.raw_data = p.raw_data or {}
                            p.raw_data["written_reviews"] = revs
                            if entry.get("product_rating_object"):
                                p.raw_data["product_rating_object"] = entry["product_rating_object"]
                            if entry.get("product_rating_count") and not p.review_count:
                                p.review_count = entry["product_rating_count"]
                except Exception as rev_err:
                    logger.warning("Failed to enrich Amazon products with reviews: %s", rev_err)

            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = len(products)
            self._last_status = "active" if products else "empty"
            self._last_message = f"Fetched {len(products)} live Amazon products via Bright Data."
            return products
        except BrightDataServiceError as exc:
            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = 0
            self._last_status = "unavailable"
            self._last_message = str(exc)
            return []
        except Exception as exc:
            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = 0
            self._last_status = "unavailable"
            self._last_message = f"Bright Data request failed: {type(exc).__name__}"
            return []


class BrightDataFlipkartProvider(BaseProductProvider):
    """Search Flipkart, then enrich direct product URLs using unified schema."""

    def __init__(self):
        super().__init__(
            provider_id="brightdata_flipkart_products",
            name="Bright Data Flipkart Products",
            marketplace="Flipkart",
        )

    def is_configured(self) -> bool:
        key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
        return bool(key) and not key.startswith("YOUR_")

    def get_required_env_keys(self) -> List[str]:
        return ["BRIGHTDATA_API_KEY"]

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, dict):
            value = value.get("amount") or value.get("value")
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return None
        import re
        match = re.search(r"\d[\d,]*(?:\.\d+)?", value)
        return float(match.group(0).replace(",", "")) if match else None

    @classmethod
    def _extract_flipkart_prices(cls, pricing_dict: Any) -> tuple[Optional[float], Optional[float], Optional[float]]:
        current = None
        original = None
        discount = None
        if isinstance(pricing_dict, dict):
            discount = pricing_dict.get("totalDiscount") or pricing_dict.get("discount")
            if "finalPrice" in pricing_dict and isinstance(pricing_dict["finalPrice"], dict):
                current = cls._number(pricing_dict["finalPrice"].get("value"))
            if "mrp" in pricing_dict and isinstance(pricing_dict["mrp"], dict):
                original = cls._number(pricing_dict["mrp"].get("value"))

            prices_list = pricing_dict.get("prices", [])
            if isinstance(prices_list, list):
                for p_item in prices_list:
                    if isinstance(p_item, dict):
                        val = cls._number(p_item.get("value"))
                        p_type = str(p_item.get("priceType", "")).upper()
                        strike = p_item.get("strikeOff", False)
                        if strike or "FSP" in p_type or "MRP" in p_type:
                            if original is None or (val and val > (original or 0)):
                                original = val
                        if not strike or "SPECIAL" in p_type or "FINAL" in p_type:
                            if current is None or (val and val < (current or 9999999)):
                                current = val
        return current, original, cls._number(discount)

    @classmethod
    def _fetch_direct_flipkart_sync(cls, query: str, limit: int = 15) -> List[dict[str, Any]]:
        import requests
        import re
        from json import JSONDecoder
        decoder = JSONDecoder()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                scripts = re.findall(r"<script[^>]*>(.*?)</script>", resp.text, re.DOTALL)
                for s in scripts:
                    if "window.__INITIAL_STATE__" in s:
                        idx = s.find("{")
                        if idx != -1:
                            data, _ = decoder.raw_decode(s[idx:])
                            slots_list = data.get("pageDataV4", {}).get("page", {}).get("data", {})
                            extracted = []
                            def walk(d):
                                if isinstance(d, dict):
                                    if "titles" in d and "pricing" in d and ("baseUrl" in d or "action" in d):
                                        extracted.append(d)
                                    for v in d.values():
                                        walk(v)
                                elif isinstance(d, list):
                                    for elem in d:
                                        walk(elem)
                            walk(slots_list)

                            results = []
                            for node in extracted:
                                base_url = node.get("baseUrl")
                                if not base_url and isinstance(node.get("action"), dict):
                                    base_url = node.get("action", {}).get("url")
                                if not base_url:
                                    continue
                                clean_path = str(base_url).lstrip("/")
                                full_url = f"https://www.flipkart.com/{clean_path}"

                                titles = node.get("titles", {})
                                title = titles.get("title") or titles.get("primaryText")
                                if not title:
                                    continue

                                brand = str(node.get("productBrand") or titles.get("superTitle") or titles.get("subtitle") or "").strip()
                                pricing = node.get("pricing", {})
                                final_price, mrp, discount = cls._extract_flipkart_prices(pricing)

                                rating_node = node.get("rating", {})
                                rating = rating_node.get("average") if isinstance(rating_node, dict) else None
                                review_count = rating_node.get("count") if isinstance(rating_node, dict) else None

                                media = node.get("media", {})
                                images = []
                                if isinstance(media, dict) and "images" in media:
                                    for img in media["images"]:
                                        if isinstance(img, dict) and "url" in img:
                                            u = img["url"].replace("{@width}", "400").replace("{@height}", "400").replace("{@quality}", "80")
                                            images.append(u)

                                item_id = str(node.get("listingId") or node.get("itemId") or node.get("id") or "")
                                avail = str(node.get("availability") or "IN_STOCK")
                                in_stock = "OUT" not in avail.upper()

                                results.append({
                                    "url": full_url,
                                    "title": title,
                                    "brand": brand,
                                    "item_id": item_id,
                                    "final_price": final_price,
                                    "mrp": mrp,
                                    "discount": discount,
                                    "star_rating": rating,
                                    "review_count": review_count,
                                    "availability": "In Stock" if in_stock else "Out of Stock",
                                    "images": images,
                                    "primary_image": images[0] if images else None,
                                    "features": node.get("keySpecs") or []
                                })
                                if len(results) >= limit:
                                    break
                            if results:
                                return results
        except Exception as e:
            logger.warning("Direct Flipkart catalog sync failed: %s", e)
        return []

    @classmethod
    def _extract_rating_and_reviews(cls, record: dict[str, Any]) -> tuple[Optional[float], Optional[int]]:
        """Safely extract star rating and review/rating count across all Flipkart record variants."""
        rating: Optional[float] = None
        review_count: Optional[int] = None

        # 1. Check nested rating dictionaries (e.g. rating: {"average": 4.3, "count": 15200})
        for key in ["rating", "ratings", "product_rating", "rating_summary", "review_summary"]:
            val = record.get(key)
            if isinstance(val, dict):
                r_avg = cls._number(
                    val.get("average") or val.get("averageRating") or val.get("rating") or val.get("stars") or val.get("value")
                )
                r_cnt = cls._number(
                    val.get("count") or val.get("totalCount") or val.get("ratingCount") or val.get("reviewCount") or val.get("ratingsCount") or val.get("reviewsCount")
                )
                if rating is None and r_avg is not None:
                    rating = r_avg
                if review_count is None and r_cnt is not None:
                    review_count = int(r_cnt)

        # 2. Check flat rating fields if not yet found
        if rating is None:
            for r_key in [
                "star_rating", "rating", "average_customer_review", "average_rating",
                "avg_rating", "rating_value", "stars", "product_rating", "user_rating",
                "averageRating", "rating_number", "score"
            ]:
                if r_key in record and not isinstance(record[r_key], (dict, list)):
                    val = cls._number(record[r_key])
                    if val is not None and 0 < val <= 5.0:
                        rating = val
                        break

        # 3. Check flat review / rating count fields if not yet found
        if review_count is None:
            for c_key in [
                "review_count", "reviews_count", "number_of_customer_reviews",
                "number_of_customer_ratings", "rating_count", "ratings_count",
                "num_reviews", "num_ratings", "total_ratings", "total_reviews",
                "reviews", "ratings", "count", "totalCount", "ratingCount", "reviewCount"
            ]:
                if c_key in record and not isinstance(record[c_key], (dict, list)):
                    cnt = cls._number(record[c_key])
                    if cnt is not None and cnt >= 0:
                        review_count = int(cnt)
                        break

        # Sanity checks
        if rating is not None and (rating <= 0 or rating > 5.0):
            rating = None
        if review_count is not None and review_count < 0:
            review_count = None

        return rating, review_count

    @classmethod
    def normalize_record(cls, record: dict[str, Any], category: str) -> Optional[NormalizedProduct]:
        product_url = record.get("url")
        title = record.get("title") or record.get("name")
        item_id = record.get("item_id") or record.get("sku") or record.get("variant_id") or product_url
        if not isinstance(title, str) or not item_id or not NormalizationService.is_direct_product_url(product_url, "Flipkart"):
            return None

        current_price, original_price, discount = NormalizationService.extract_product_prices(record)
        availability_value = record.get("availability")
        availability = "In Stock" if availability_value in (True, 1, "1", "in_stock", "In Stock") else "Out of Stock" if availability_value in (False, 0, "0", "out_of_stock") else str(availability_value or "In Stock")
        rating, reviews = cls._extract_rating_and_reviews(record)
        brand = str(record.get("brand") or "")
        flipkart_image_keys = [
            "primary_image",
            "image_url",
            "image",
            "main_image",
            "thumbnail",
            "image_link",
            "image_urls",
            "additional_image_urls",
            "additional_images",
            "images",
            "product_images",
        ]
        image_candidates = NormalizationService.extract_image_candidates(record, flipkart_image_keys)
        image_url = image_candidates[0] if image_candidates else ""

        product = NormalizedProduct(
            id=f"brightdata_flipkart_{item_id}", source_product_id=str(item_id), title=title.strip(), brand=brand,
            category=category, image_url=image_url, image_candidates=image_candidates, current_price=current_price, original_price=original_price,
            discount_percent=discount, currency="INR", rating=rating, review_count=int(reviews) if reviews is not None else None,
            availability=availability, product_url=product_url, marketplace="Flipkart", provider="brightdata_flipkart_products",
            seller=record.get("store_name") or record.get("seller") or "Flipkart Seller", source="Bright Data Flipkart Live Products",
            specifications={"Brand": brand} if brand else {}, features=record.get("features") if isinstance(record.get("features"), list) else [], raw_data=record,
            offers=[MarketplaceOffer(
                marketplace="Flipkart", provider="brightdata_flipkart_products", product_url=product_url,
                current_price=current_price, original_price=original_price, discount_percent=discount, currency="INR",
                in_stock=availability_value in (True, 1, "1", "in_stock", "In Stock") if availability_value is not None else True,
                rating=rating, review_count=int(reviews) if reviews is not None else None, seller_name=record.get("store_name") or "Flipkart Seller",
            )],
        )
        return NormalizationService.normalize_product(product)

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        started = time.time()
        if not self.is_configured():
            self._last_status, self._last_items_count = "credentials_required", 0
            self._last_message = "Bright Data API key required in BRIGHTDATA_API_KEY."
            return []
        try:
            discovered_urls = []
            try:
                discovered_urls = await asyncio.to_thread(search_flipkart_product_urls, query)
            except BrightDataServiceError as exc:
                if exc.status_code == 403 or "denied" in str(exc).lower():
                    raise
                logger.info("Bright Data Flipkart trigger returned status=%s; falling back to direct catalog sync", exc.status_code)
            
            direct_urls = [url for url in discovered_urls if NormalizationService.is_direct_product_url(url, "Flipkart")][:limit]
            products = []
            if direct_urls:
                fetched_records = await asyncio.to_thread(fetch_flipkart_products, direct_urls)
                products = [product for record in fetched_records if (product := self.normalize_record(record, category)) is not None]
            if not products:
                # Direct catalog fallback
                direct_records = await asyncio.to_thread(self._fetch_direct_flipkart_sync, query, limit)
                products = [p for r in direct_records if (p := self.normalize_record(r, category)) is not None]
            self._last_items_count = len(products)
            self._last_status = "active" if products else "empty"
            self._last_message = f"Fetched {len(products)} live Flipkart products."
            return products
        except BrightDataServiceError as exc:
            self._last_status, self._last_items_count = "unavailable", 0
            self._last_message = str(exc)
            return []
        except Exception as exc:
            self._last_status, self._last_items_count = "unavailable", 0
            self._last_message = f"Bright Data Flipkart request failed: {type(exc).__name__}"
            return []
        finally:
            self._last_latency_ms = (time.time() - started) * 1000
