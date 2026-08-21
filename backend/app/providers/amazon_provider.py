import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.providers.base import BaseProductProvider
from app.services.normalization_service import NormalizationService


class AmazonCreatorsAPIProvider(BaseProductProvider):
    """Amazon Creators API product search for the India marketplace."""

    def __init__(self):
        super().__init__(
            provider_id="amazon_creators_india",
            name="Amazon India Creators API",
            marketplace="Amazon India",
        )
        self.endpoint = "https://creatorsapi.amazon/catalog/v1/searchItems"
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0

    def is_configured(self) -> bool:
        return bool(
            settings.AMAZON_CREATORS_CREDENTIAL_ID
            and settings.AMAZON_CREATORS_CREDENTIAL_SECRET
            and settings.AMAZON_CREATORS_CREDENTIAL_VERSION
            and settings.AMAZON_CREATORS_PARTNER_TAG
        )

    def get_required_env_keys(self) -> List[str]:
        return [
            "AMAZON_CREATORS_CREDENTIAL_ID",
            "AMAZON_CREATORS_CREDENTIAL_SECRET",
            "AMAZON_CREATORS_CREDENTIAL_VERSION",
            "AMAZON_CREATORS_PARTNER_TAG",
        ]

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        now = time.time()
        if self._access_token and now < self._token_expires_at - 60:
            return self._access_token

        response = await client.post(
            settings.AMAZON_CREATORS_TOKEN_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={
                "grant_type": "client_credentials",
                "client_id": settings.AMAZON_CREATORS_CREDENTIAL_ID,
                "client_secret": settings.AMAZON_CREATORS_CREDENTIAL_SECRET,
                "scope": "creatorsapi::default",
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f"Creators API token request returned HTTP {response.status_code}")

        token_data = response.json()
        token = token_data.get("access_token")
        if not token:
            raise ValueError("Creators API token response did not include access_token")
        self._access_token = token
        self._token_expires_at = now + float(token_data.get("expires_in", 3600))
        return token

    @staticmethod
    def _nested(data: Dict[str, Any], *keys: str) -> Any:
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    @classmethod
    def _image_url(cls, item: Dict[str, Any]) -> str:
        images = item.get("images", {}).get("primary", {})
        for size in ("hiRes", "large", "medium", "small"):
            url = cls._nested(images, size, "url")
            if url:
                return url
        return ""

    @classmethod
    def _offer_values(cls, item: Dict[str, Any]):
        listings = cls._nested(item, "offersV2", "listings") or []
        listing = listings[0] if listings else {}
        price = cls._nested(listing, "price", "amount")
        original_price = cls._nested(listing, "price", "savings", "amount")
        availability = cls._nested(listing, "availability", "message") or "Unknown"
        return price, original_price, availability

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "Amazon Creators API requires Credential ID, Credential Secret, Version, and Partner Tag."
            self._last_items_count = 0
            return []

        payload = {
            "keywords": query,
            "partnerTag": settings.AMAZON_CREATORS_PARTNER_TAG,
            "marketplace": "www.amazon.in",
            "resources": [
                "images.primary",
                "itemInfo.title",
                "itemInfo.byLineInfo",
                "itemInfo.features",
                "customerReviews.count",
                "customerReviews.starRating",
                "offersV2",
            ],
            "itemCount": min(limit, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                token = await self._get_access_token(client)
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "x-marketplace": "www.amazon.in",
                    },
                    json=payload,
                )
                self._last_latency_ms = (time.time() - start_time) * 1000
                if response.status_code != 200:
                    self._last_status = "error"
                    self._last_message = f"Amazon Creators API returned HTTP {response.status_code}"
                    self._last_items_count = 0
                    return []

                data = response.json()
                items = self._nested(data, "itemsResult", "items") or []
                products: List[NormalizedProduct] = []
                for item in items:
                    asin = item.get("asin")
                    title = self._nested(item, "itemInfo", "title", "displayValue")
                    product_url = item.get("detailPageURL")
                    if not asin or not title or not NormalizationService.is_direct_product_url(product_url, "Amazon India"):
                        continue

                    brand = self._nested(item, "itemInfo", "byLineInfo", "brand", "displayValue") or "Unknown Brand"
                    features = self._nested(item, "itemInfo", "features", "displayValues") or []
                    rating = self._nested(item, "customerReviews", "starRating", "value")
                    review_count = self._nested(item, "customerReviews", "count")
                    current_price, original_price, availability = self._offer_values(item)
                    discount = None
                    if current_price and original_price and original_price > current_price:
                        discount = round((original_price - current_price) / original_price * 100, 1)

                    product_kwargs = {
                        "id": f"amzn_{asin}",
                        "source_product_id": asin,
                        "title": title,
                        "brand": brand,
                        "description": self._nested(item, "itemInfo", "contentInfo", "displayValue"),
                        "category": category,
                        "image_url": self._image_url(item),
                        "current_price": float(current_price) if current_price is not None else None,
                        "original_price": float(original_price) if original_price is not None else None,
                        "discount_percent": discount,
                        "currency": "INR",
                        "rating": float(rating) if rating is not None else None,
                        "review_count": int(review_count) if review_count is not None else None,
                        "availability": availability,
                        "product_url": product_url,
                        "marketplace": "Amazon India",
                        "provider": self.provider_id,
                        "seller": None,
                        "source": "Amazon India Creators API",
                        "specifications": {"ASIN": asin, "Brand": brand},
                        "features": features,
                        "raw_data": item,
                    }
                    product_kwargs["offers"] = [MarketplaceOffer(
                        marketplace="Amazon India",
                        provider=self.provider_id,
                        product_url=product_url,
                        current_price=product_kwargs["current_price"],
                        original_price=product_kwargs["original_price"],
                        discount_percent=discount,
                        currency="INR",
                        in_stock="in stock" in availability.lower() if availability != "Unknown" else None,
                        rating=product_kwargs["rating"],
                        review_count=product_kwargs["review_count"],
                        seller_name=None,
                    )]
                    products.append(NormalizedProduct(**product_kwargs))

                self._last_items_count = len(products)
                self._last_status = "active" if products else "empty"
                self._last_message = f"Amazon Creators API returned {len(products)} product records."
                return products
        except httpx.TimeoutException:
            self._last_status = "unavailable"
            self._last_message = "Amazon Creators API request timed out."
            self._last_items_count = 0
            return []
        except (ValueError, TypeError):
            self._last_status = "error"
            self._last_message = "Amazon Creators API returned an invalid response."
            self._last_items_count = 0
            return []
        except Exception as error:
            self._last_status = "unavailable"
            self._last_message = f"Amazon Creators API request failed: {type(error).__name__}"
            self._last_items_count = 0
            return []
        finally:
            self._last_latency_ms = (time.time() - start_time) * 1000
