import time
from typing import List
import httpx
from app.core.config import settings
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider

class FlipkartAffiliateProvider(BaseProductProvider):
    """
    Official Flipkart Affiliate Product Search API
    Uses FK-Affiliate-Id and FK-Affiliate-Token headers for authentication.
    """
    def __init__(self):
        super().__init__(
            provider_id="flipkart_affiliate",
            name="Flipkart Official Affiliate API",
            marketplace="Flipkart"
        )
        self.endpoint = "https://affiliate-api.flipkart.net/affiliate/1.0/search.json"

    def is_configured(self) -> bool:
        return bool(settings.FLIPKART_AFFILIATE_ID and settings.FLIPKART_AFFILIATE_TOKEN)

    def get_required_env_keys(self) -> List[str]:
        return ["FLIPKART_AFFILIATE_ID", "FLIPKART_AFFILIATE_TOKEN"]

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "Live Flipkart Affiliate API requires FLIPKART_AFFILIATE_ID and FLIPKART_AFFILIATE_TOKEN."
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_items_count = 0
            return []

        headers = {
            "Fk-Affiliate-Id": settings.FLIPKART_AFFILIATE_ID,
            "Fk-Affiliate-Token": settings.FLIPKART_AFFILIATE_TOKEN,
            "Accept": "application/json"
        }
        params = {
            "query": query,
            "resultCount": min(limit, 10)
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    product_list = data.get("products", [])
                    products = []
                    
                    for item in product_list:
                        base_info = item.get("productBaseInfoV1", {})
                        product_id = base_info.get("productId", "")
                        title = base_info.get("title", "")
                        brand = base_info.get("productBrand", "Generic")
                        product_url = base_info.get("productUrl", f"https://www.flipkart.com/item/p/{product_id}")
                        
                        # Images
                        image_dict = base_info.get("imageUrls", {})
                        image_url = image_dict.get("800x800") or image_dict.get("400x400") or image_dict.get("200x200") or ""
                        
                        # Price
                        pricing = base_info.get("flipkartSellingPrice", {})
                        current_price = float(pricing.get("amount")) if "amount" in pricing else None
                        mrp = base_info.get("maximumRetailPrice", {})
                        original_price = float(mrp.get("amount")) if "amount" in mrp else None
                        discount = None
                        if original_price and current_price and original_price > current_price > 0:
                            discount = round(((original_price - current_price) / original_price) * 100, 1)
                            
                        # Rating
                        rating = float(base_info.get("productRating")) if base_info.get("productRating") else None
                        review_count = int(base_info.get("productReviewCount")) if base_info.get("productReviewCount") else None
                        in_stock = base_info.get("inStock", True)
                        
                        features_list = base_info.get("keySpecs", [])
                        
                        norm_prod = NormalizedProduct(
                            id=f"fk_{product_id}",
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
                            availability="In Stock" if in_stock else "Out of Stock",
                            product_url=product_url,
                            marketplace="Flipkart",
                            provider=self.provider_id,
                            seller="Flipkart Assured",
                            source="Flipkart Official Affiliate API",
                            specifications={"FSN": product_id, "Brand": brand},
                            features=features_list,
                            offers=[
                                MarketplaceOffer(
                                    marketplace="Flipkart",
                                    provider=self.provider_id,
                                    product_url=product_url,
                                    current_price=current_price,
                                    original_price=original_price,
                                    discount_percent=discount,
                                    currency="INR",
                                    in_stock=in_stock,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name="Flipkart Assured"
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active"
                    self._last_message = f"Successfully retrieved {len(products)} live products from Flipkart Affiliate API."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"Flipkart API returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Error connecting to Flipkart Affiliate API: {str(e)}"
            return []
