import time
import re
from typing import List
import httpx
from app.core.config import settings
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider
from app.services.normalization_service import NormalizationService

class SerpApiShoppingProvider(BaseProductProvider):
    """
    SerpApi Google Shopping India Integration
    Searches live products from Indian merchants (Amazon.in, Flipkart, Croma, Reliance Digital) in INR.
    """
    def __init__(self):
        super().__init__(
            provider_id="serpapi_shopping_india",
            name="SerpApi Multi-Merchant Shopping India",
            marketplace="Multi-Marketplace (Amazon/Flipkart)"
        )
        self.endpoint = "https://serpapi.com/search"

    def is_configured(self) -> bool:
        return bool(settings.SERPAPI_KEY)

    def get_required_env_keys(self) -> List[str]:
        return ["SERPAPI_KEY"]

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "SerpApi Key required in SERPAPI_KEY environment variable."
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_items_count = 0
            return []

        params = {
            "engine": "google_shopping",
            "q": query,
            "location": "India",
            "gl": "in",
            "hl": "en",
            "api_key": settings.SERPAPI_KEY,
            "num": min(limit, 15)
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, params=params)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    shopping_results = data.get("shopping_results", [])
                    products = []
                    
                    for item in shopping_results[:limit]:
                        title = item.get("title", "")
                        source = item.get("source", "Retailer")
                        product_url = item.get("link", "") or item.get("product_link", "")
                        image_url = item.get("thumbnail", "")
                        
                        price_str = str(item.get("extracted_price", item.get("price", "")))
                        clean_p = re.sub(r'[^\d.]', '', price_str) if price_str else ""
                        current_price = float(clean_p) if clean_p else None
                        
                        orig_str = str(item.get("extracted_old_price", item.get("old_price", "")))
                        clean_orig = re.sub(r'[^\d.]', '', orig_str) if orig_str else ""
                        original_price = float(clean_orig) if clean_orig else None
                        
                        discount = None
                        if original_price and current_price and original_price > current_price > 0:
                            discount = round(((original_price - current_price) / original_price) * 100, 1)
                            
                        rating = float(item.get("rating")) if item.get("rating") else None
                        review_count = int(item.get("reviews")) if item.get("reviews") else None
                        
                        # Map source to marketplace
                        marketplace = "Amazon India" if "amazon" in source.lower() else ("Flipkart" if "flipkart" in source.lower() else source)
                        if not NormalizationService.is_direct_product_url(product_url, marketplace):
                            continue
                        
                        brand = item.get("brand") or "Unknown Brand"
                        
                        features_list = [f"Listed by {source}"]
                        if current_price:
                            features_list.append(f"Price: ₹{current_price:,.0f}")
                        
                        norm_prod = NormalizedProduct(
                            id=f"serp_{item.get('position', 0)}_{int(current_price) if current_price else 'item'}",
                            source_product_id=str(item.get("product_id") or item.get("position") or ""),
                            title=title,
                            brand=brand,
                            category=category,
                            image_url=image_url,
                            current_price=current_price,
                            original_price=original_price,
                            discount_percent=discount,
                            currency="INR",
                            rating=rating,
                            review_count=review_count,
                            availability=item.get("availability") or "Unknown",
                            product_url=product_url,
                            marketplace=marketplace,
                            provider=self.provider_id,
                            seller=source,
                            source=f"SerpApi Google Shopping India ({source})",
                            specifications={"Source": source, "Brand": brand},
                            features=features_list,
                            raw_data=item,
                            offers=[
                                MarketplaceOffer(
                                    marketplace=marketplace,
                                    provider=self.provider_id,
                                    product_url=product_url,
                                    current_price=current_price,
                                    original_price=original_price,
                                    discount_percent=discount,
                                    currency="INR",
                                    in_stock=None,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name=source
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active"
                    self._last_message = f"Fetched {len(products)} live shopping items via SerpApi."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"SerpApi returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"SerpApi error: {str(e)}"
            return []
