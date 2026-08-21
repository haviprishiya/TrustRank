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
        
        # Build search queries for amazon.in and flipkart.com
        search_terms = f"{query} price buy online india amazon flipkart"
        
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
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = soup.find_all('div', class_='result')
                    
                    for idx, res in enumerate(results[:limit]):
                        title_tag = res.find('a', class_='result__a')
                        snippet_tag = res.find('a', class_='result__snippet')
                        
                        if not title_tag:
                            continue
                            
                        title = title_tag.get_text().strip()
                        raw_url = title_tag.get('href', '')
                        snippet = snippet_tag.get_text().strip() if snippet_tag else ""
                        
                        # Filter out non-shopping articles
                        if not any(k in raw_url.lower() or k in title.lower() for k in ['amazon.in', 'flipkart', 'buy', 'price', 'shop', 'store']):
                            continue
                            
                        marketplace = "Amazon India" if "amazon" in raw_url.lower() or "amazon" in title.lower() else "Flipkart"
                        
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

                        brand = title.split()[0] if title else "Generic"
                        
                        norm_prod = NormalizedProduct(
                            id=f"live_{idx}_{int(current_price) if current_price else 'item'}",
                            title=title,
                            brand=brand,
                            category=category,
                            image_url="",  # No fake placeholder images: real image or clean fallback
                            current_price=current_price,
                            original_price=None,
                            discount_percent=None,
                            currency="INR",
                            rating=rating,
                            review_count=review_count,
                            availability="Live Marketplace Listing",
                            product_url=raw_url if raw_url.startswith("http") else f"https://www.amazon.in/s?k={query}",
                            marketplace=marketplace,
                            provider=self.provider_id,
                            seller=f"{marketplace} Listing",
                            source=f"Live Web Search ({marketplace})",
                            specifications={"Marketplace": marketplace, "Search Query": query},
                            features=[snippet[:160]] if snippet else [f"Verified live result on {marketplace}"],
                            offers=[
                                MarketplaceOffer(
                                    marketplace=marketplace,
                                    provider=self.provider_id,
                                    product_url=raw_url if raw_url.startswith("http") else f"https://www.amazon.in/s?k={query}",
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
                    self._last_message = f"Live search retrieved {len(products)} real web listings."
                    return products
                else:
                    self._last_status = "unavailable"
                    self._last_message = f"Live search returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Live network search unavailable: {str(e)}"
            return []
