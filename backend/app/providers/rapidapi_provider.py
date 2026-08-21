import time
import re
from typing import List, Optional
import httpx
from app.core.config import settings
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider
from app.services.normalization_service import NormalizationService

class RapidApiAmazonProvider(BaseProductProvider):
    """
    RapidAPI Real-Time Amazon India Data API
    Retrieves live real-time product data, ASINs, prices in INR, ratings, and URLs.
    """
    def __init__(self):
        super().__init__(
            provider_id="rapidapi_amazon_india",
            name="RapidAPI Real-Time Amazon India",
            marketplace="Amazon India"
        )
        self.host = settings.RAPIDAPI_AMAZON_HOST or "real-time-amazon-data.p.rapidapi.com"
        self.endpoint = f"https://{self.host}/search"

    def is_configured(self) -> bool:
        return bool(settings.RAPIDAPI_KEY)

    def get_required_env_keys(self) -> List[str]:
        return ["RAPIDAPI_KEY"]

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "RapidAPI Key required in RAPIDAPI_KEY environment variable."
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_items_count = 0
            return []

        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.host
        }
        params = {
            "query": query,
            "page": "1",
            "country": "IN",
            "sort_by": "RELEVANCE"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Could be data.data.products or data.products
                    prod_data = data.get("data", {}).get("products", []) or data.get("products", [])
                    products = []
                    
                    for item in prod_data[:limit]:
                        asin = item.get("asin", "")
                        title = item.get("product_title", "")
                        product_url = item.get("product_url") or (f"https://www.amazon.in/dp/{asin}" if asin else None)
                        if not asin or not title or not NormalizationService.is_direct_product_url(product_url, "Amazon India"):
                            continue
                        image_url = item.get("product_photo", "") or item.get("product_main_image_url", "")
                        
                        price_str = item.get("product_price", "")
                        clean_price = re.sub(r'[^\d.]', '', price_str) if price_str else ""
                        current_price = float(clean_price) if clean_price else None
                        
                        orig_str = item.get("product_original_price", "")
                        clean_orig = re.sub(r'[^\d.]', '', orig_str) if orig_str else ""
                        original_price = float(clean_orig) if clean_orig else None
                        
                        discount = None
                        if original_price and current_price and original_price > current_price > 0:
                            discount = round(((original_price - current_price) / original_price) * 100, 1)
                            
                        rating = float(item.get("product_star_rating")) if item.get("product_star_rating") else None
                        review_count = int(item.get("product_num_ratings")) if item.get("product_num_ratings") else None
                        
                        brand = item.get("product_byline", "").replace("Brand: ", "").strip()
                        if not brand or brand.lower() == "brand":
                            brand = title.split()[0] if title else "Generic"
                            
                        norm_prod = NormalizedProduct(
                            id=f"amzn_rapid_{asin}",
                            source_product_id=asin,
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
                            marketplace="Amazon India",
                            provider=self.provider_id,
                            seller=None,
                            source="RapidAPI Real-Time Amazon India Data",
                            specifications={"ASIN": asin, "Brand": brand},
                            features=[f"Amazon India Live Listing • ASIN: {asin}"],
                            raw_data=item,
                            offers=[
                                MarketplaceOffer(
                                    marketplace="Amazon India",
                                    provider=self.provider_id,
                                    product_url=product_url,
                                    current_price=current_price,
                                    original_price=original_price,
                                    discount_percent=discount,
                                    currency="INR",
                                    in_stock=None,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name=None
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active"
                    self._last_message = f"Fetched {len(products)} live products via RapidAPI Amazon Data."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"RapidAPI Amazon returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"RapidAPI Amazon error: {str(e)}"
            return []


class RapidApiFlipkartProvider(BaseProductProvider):
    """
    RapidAPI Real-Time Flipkart Data API
    Retrieves live Flipkart products, prices in INR, ratings, and URLs.
    """
    def __init__(self):
        super().__init__(
            provider_id="rapidapi_flipkart",
            name="RapidAPI Real-Time Flipkart",
            marketplace="Flipkart"
        )
        self.host = settings.RAPIDAPI_FLIPKART_HOST or "real-time-flipkart-data.p.rapidapi.com"
        self.endpoint = f"https://{self.host}/search"

    def is_configured(self) -> bool:
        return bool(settings.RAPIDAPI_KEY)

    def get_required_env_keys(self) -> List[str]:
        return ["RAPIDAPI_KEY"]

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "RapidAPI Key required in RAPIDAPI_KEY environment variable."
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_items_count = 0
            return []

        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.host
        }
        params = {
            "query": query,
            "page": "1"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    prod_data = data.get("products", []) or data.get("data", [])
                    products = []
                    
                    for idx, item in enumerate(prod_data[:limit]):
                        title = item.get("title", "") or item.get("name", "")
                        product_id = item.get("product_id") or item.get("productId") or item.get("id")
                        product_url = item.get("url") or item.get("product_url")
                        if not product_id or not title or not NormalizationService.is_direct_product_url(product_url, "Flipkart"):
                            continue
                        image_url = item.get("image", "") or item.get("thumbnail", "")
                        
                        price_str = str(item.get("price", ""))
                        clean_price = re.sub(r'[^\d.]', '', price_str) if price_str else ""
                        current_price = float(clean_price) if clean_price else None
                        
                        orig_str = str(item.get("original_price", ""))
                        clean_orig = re.sub(r'[^\d.]', '', orig_str) if orig_str else ""
                        original_price = float(clean_orig) if clean_orig else None
                        
                        discount = None
                        if original_price and current_price and original_price > current_price > 0:
                            discount = round(((original_price - current_price) / original_price) * 100, 1)
                            
                        rating = float(item.get("rating")) if item.get("rating") else None
                        review_count = int(item.get("reviews_count")) if item.get("reviews_count") else None
                        
                        brand = item.get("brand", "")
                        if not brand:
                            brand = title.split()[0] if title else "Generic"
                            
                        norm_prod = NormalizedProduct(
                            id=f"fk_rapid_{product_id}",
                            source_product_id=str(product_id),
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
                            marketplace="Flipkart",
                            provider=self.provider_id,
                            seller=None,
                            source="RapidAPI Real-Time Flipkart Data",
                            specifications={"Brand": brand},
                            features=[f"Flipkart Live Listing • Brand: {brand}"],
                            raw_data=item,
                            offers=[
                                MarketplaceOffer(
                                    marketplace="Flipkart",
                                    provider=self.provider_id,
                                    product_url=product_url,
                                    current_price=current_price,
                                    original_price=original_price,
                                    discount_percent=discount,
                                    currency="INR",
                                    in_stock=None,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name=None
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active"
                    self._last_message = f"Fetched {len(products)} live products via RapidAPI Flipkart Data."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"RapidAPI Flipkart returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"RapidAPI Flipkart error: {str(e)}"
            return []
