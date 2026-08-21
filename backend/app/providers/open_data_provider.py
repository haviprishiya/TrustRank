import time
from typing import List
import httpx
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider
from app.core.config import settings

class OpenBeautyFactsProvider(BaseProductProvider):
    """
    Open Beauty Facts & Open Product Data API
    Retrieves real live skincare & cosmetics products, ingredients, brands, barcodes, and specs.
    """
    def __init__(self):
        super().__init__(
            provider_id="open_beauty_facts",
            name="Open Beauty Facts Live Database",
            marketplace="Verified Beauty Registry"
        )
        self.endpoint = "https://world.openbeautyfacts.org/cgi/search.pl"

    def is_configured(self) -> bool:
        return settings.ENABLE_OPEN_DATA_PROVIDER

    def is_enabled(self) -> bool:
        return settings.ENABLE_OPEN_DATA_PROVIDER

    def get_required_env_keys(self) -> List[str]:
        return []

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        
        # Only run for skincare / beauty / personal care
        if category not in ("skincare", "general"):
            self._last_status = "idle"
            self._last_message = f"Skipped for category '{category}'"
            self._last_items_count = 0
            return []

        params = {
            "search_terms": query,
            "search_simple": "1",
            "action": "process",
            "json": "1",
            "page_size": min(limit, 12)
        }
        headers = {
            "User-Agent": "TrustRankShoppingAssistant/1.0 (contact@trustrank.org)"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint, params=params, headers=headers)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    products_raw = data.get("products", [])
                    products = []
                    
                    for item in products_raw:
                        code = item.get("code", "")
                        name = item.get("product_name", "") or item.get("product_name_en", "")
                        if not code or not name or len(name) < 3:
                            continue
                            
                        brand = item.get("brands", "").split(",")[0].strip() or "Unknown Brand"
                        image_url = item.get("image_front_url", "") or item.get("image_url", "")
                        
                        # Real ingredients list if present
                        ingredients_text = item.get("ingredients_text", "")
                        features = []
                        if ingredients_text:
                            features.append(f"Key Actives: {ingredients_text[:120]}...")
                        categories_tags = item.get("categories_tags", [])
                        if categories_tags:
                            features.append(f"Type: {', '.join(categories_tags[:2]).replace('en:', '').title()}")
                            
                        norm_prod = NormalizedProduct(
                            id=f"obf_{code}",
                            title=f"{brand} {name}",
                            brand=brand,
                            category="skincare",
                            image_url=image_url,
                            current_price=None,
                            original_price=None,
                            discount_percent=None,
                            currency="INR",
                            rating=None,
                            review_count=None,
                            availability="Unknown",
                            product_url=f"https://world.openbeautyfacts.org/product/{code}",
                            marketplace="Open Beauty Facts",
                            provider=self.provider_id,
                            seller="Verified Cosmetic Registry",
                            source="Open Beauty Facts Live Database",
                            specifications={"Barcode / EAN": code, "Brand": brand, "Ingredients": ingredients_text[:120] if ingredients_text else "Formula registered"},
                            features=features if features else ["Dermatologically registered formulation"],
                            offers=[
                                MarketplaceOffer(
                                    marketplace="Open Beauty Facts",
                                    provider=self.provider_id,
                                    product_url=f"https://world.openbeautyfacts.org/product/{code}",
                                    current_price=None,
                                    original_price=None,
                                    discount_percent=None,
                                    currency="INR",
                                    in_stock=None,
                                    rating=None,
                                    review_count=None,
                                    seller_name="Verified Formulation Registry"
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active" if products else "empty"
                    self._last_message = f"Found {len(products)} products in Open Beauty Facts registry."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"Open Beauty Facts API returned HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Open Beauty Facts error: {str(e)}"
            return []
