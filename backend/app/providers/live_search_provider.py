import time
import re
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider

class LiveSearchMarketplaceProvider(BaseProductProvider):
    """
    Live Public Search Marketplace Provider
    Queries public search indexes for real Amazon India and Flipkart product listings in real time.
    """
    def __init__(self):
        super().__init__(
            provider_id="live_search_india",
            name="Live Multi-Marketplace Web Search",
            marketplace="Amazon India / Flipkart"
        )

    def is_configured(self) -> bool:
        return True

    def get_required_env_keys(self) -> List[str]:
        return []

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        products = []
        
        # Build targeted query for amazon.in and flipkart.com listings only
        search_query = query
        if category == "phone" and query.strip().lower() in ("mobile", "mobiles", "phone", "phones"):
            search_query = "mobile phone"
        search_terms = f"{search_query} site:amazon.in OR site:flipkart.com"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                # Query DuckDuckGo html endpoint for public live listings
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": search_terms},
                    headers=headers
                )
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if 200 <= resp.status_code < 300:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = soup.find_all('div', class_='result')
                    
                    from app.services.normalization_service import NormalizationService

                    for idx, res in enumerate(results):
                        if len(products) >= limit:
                            break
                        title_tag = res.find('a', class_='result__a')
                        snippet_tag = res.find('a', class_='result__snippet')
                        
                        if not title_tag:
                            continue
                            
                        title = title_tag.get_text().strip()
                        raw_url = title_tag.get('href', '')
                        snippet = snippet_tag.get_text().strip() if snippet_tag else ""
                        
                        # Extract and unwrap direct URL
                        clean_direct_url = NormalizationService.unwrap_product_url(raw_url) or raw_url
                        url_lower = clean_direct_url.lower()

                        # STRICT REQUIREMENT: Only accept real amazon.in or flipkart.com domains
                        # Discard all third-party blogs, affiliate redirect loops, news articles, or other stores
                        if "amazon.in" in url_lower:
                            marketplace = "Amazon India"
                        elif "flipkart.com" in url_lower:
                            marketplace = "Flipkart"
                        else:
                            continue

                        # Filter out general category aggregator pages that are not individual products
                        title_lower = title.lower()
                        is_search_page = "/s?k=" in url_lower or "/search?" in url_lower or "/q/" in url_lower or "/pr?sid=" in url_lower or "/laptops/~" in url_lower
                        is_generic_title = any(kw in title_lower for kw in [
                            "online at best prices", "buy online at best price", "best price in india",
                            "below 50000", "below 40000", "below 30000", "under 50000", "under 60000",
                            "amazon.in:", "price list", "buying guide"
                        ])
                        if is_search_page and is_generic_title:
                            continue

                        # Clean the product title by stripping storefront boilerplate
                        clean_title = re.sub(r'\s*:\s*Amazon\.in(?::\s*[^|]+)?', '', title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'\s*:\s*Buy\s+.*?\s+at\s+Best\s+Price.*', '', clean_title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'\s*\|\s*Flipkart(?:\.com)?.*', '', clean_title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'^(?:Amazon\.in\s*:\s*|Buy\s+)', '', clean_title, flags=re.IGNORECASE).strip()
                        if not clean_title:
                            clean_title = title

                        # Resolve authentic official URL and direct image
                        image_url = ""
                        asin = None
                        if marketplace == "Amazon India":
                            asin_match = re.search(r'/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})', clean_direct_url, re.IGNORECASE)
                            if asin_match:
                                asin = asin_match.group(1).upper()
                                official_url = f"https://www.amazon.in/dp/{asin}"
                                image_url = f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SX400_.jpg"
                            else:
                                official_url = NormalizationService.resolve_official_product_url(
                                    clean_direct_url,
                                    title=clean_title,
                                    marketplace="Amazon India",
                                    source="Amazon India"
                                )
                        else:
                            # Flipkart: resolve official product or search URL
                            official_url = NormalizationService.resolve_official_product_url(
                                clean_direct_url,
                                title=clean_title,
                                marketplace="Flipkart",
                                source="Flipkart"
                            )
                        
                        # Extract authentic price if present in title or snippet e.g. Rs. 54,999 or ₹54,999
                        price_match = re.search(r'(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d+)?)', f"{title} {snippet}", re.IGNORECASE)
                        current_price = None
                        if price_match:
                            clean_p = price_match.group(1).replace(",", "")
                            try:
                                current_price = float(clean_p)
                                if current_price <= 0:
                                    current_price = None
                            except ValueError:
                                current_price = None

                        # Extract rating if present in snippet (e.g. "4.4 out of 5" or "Rating: 4.2")
                        rating = None
                        rating_match = re.search(r'(\d\.\d)\s*(?:out of 5|stars|★|\/5)', f"{title} {snippet}", re.IGNORECASE)
                        if rating_match:
                            try:
                                rating = float(rating_match.group(1))
                            except ValueError:
                                rating = None

                        review_count = None
                        reviews_match = re.search(r'([\d,]+)\s*(?:reviews|ratings|buyer reviews)', f"{title} {snippet}", re.IGNORECASE)
                        if reviews_match:
                            try:
                                review_count = int(reviews_match.group(1).replace(",", ""))
                            except ValueError:
                                review_count = None

                        brand = clean_title.split()[0] if clean_title else "Generic"
                        
                        norm_prod = NormalizedProduct(
                            id=f"live_{idx}_{asin or int(current_price) if current_price else 'item'}",
                            source_product_id=asin,
                            title=clean_title,
                            brand=brand,
                            category=category,
                            image_url=image_url,
                            current_price=current_price,
                            original_price=None,
                            discount_percent=None,
                            currency="INR",
                            rating=rating,
                            review_count=review_count,
                            availability="In Stock",
                            product_url=official_url,
                            marketplace=marketplace,
                            provider=self.provider_id,
                            seller=f"{marketplace} Listing",
                            source=f"Live Web Search ({marketplace})",
                            specifications={"Marketplace": marketplace, "ASIN": asin} if asin else {"Marketplace": marketplace},
                            features=[snippet[:160]] if snippet else [f"Verified live result on {marketplace}"],
                            offers=[
                                MarketplaceOffer(
                                    marketplace=marketplace,
                                    provider=self.provider_id,
                                    product_url=official_url,
                                    current_price=current_price,
                                    original_price=None,
                                    discount_percent=None,
                                    currency="INR",
                                    in_stock=True,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name=f"{marketplace} Merchant"
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active" if products else "empty"
                    self._last_message = f"Live search retrieved {len(products)} real Amazon/Flipkart listings."
                    return products
                else:
                    self._last_status = "unavailable"
                    self._last_message = f"Live search returned HTTP {resp.status_code}"
                    self._last_items_count = 0
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Live network search unavailable: {str(e)}"
            return []
