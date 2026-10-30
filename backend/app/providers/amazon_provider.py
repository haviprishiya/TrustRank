import time
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from app.core.config import settings
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.providers.base import BaseProductProvider

class AmazonPAAPIProvider(BaseProductProvider):
    """
    Official Amazon Product Advertising API 5.0 (India: webservices.amazon.in)
    Uses AWS Signature Version 4 HMAC-SHA256 for authenticating live requests.
    """
    def __init__(self):
        super().__init__(
            provider_id="amazon_paapi_india",
            name="Amazon India Official PA-API 5.0",
            marketplace="Amazon India"
        )
        self.host = "webservices.amazon.in"
        self.region = settings.AMAZON_PAAPI_REGION or "eu-west-1" # PAAPI for India uses eu-west-1 or in
        self.service = "ProductAdvertisingAPI"
        self.endpoint = f"https://{self.host}/paapi5/searchitems"

    def is_configured(self) -> bool:
        return bool(
            settings.AMAZON_PAAPI_ACCESS_KEY and 
            settings.AMAZON_PAAPI_SECRET_KEY and 
            settings.AMAZON_PAAPI_TAG
        )

    def get_required_env_keys(self) -> List[str]:
        return ["AMAZON_PAAPI_ACCESS_KEY", "AMAZON_PAAPI_SECRET_KEY", "AMAZON_PAAPI_TAG"]

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        k_date = self._sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, region_name)
        k_service = self._sign(k_region, service_name)
        k_signing = self._sign(k_service, 'aws4_request')
        return k_signing

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        
        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = "Live Amazon India PA-API 5.0 access requires AMAZON_PAAPI_ACCESS_KEY, AMAZON_PAAPI_SECRET_KEY, and AMAZON_PAAPI_TAG."
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_items_count = 0
            return []

        payload = {
            "Keywords": query,
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "ItemInfo.Features",
                "ItemInfo.ProductInfo",
                "ItemInfo.TechnicalInfo",
                "Offers.Listings.Price",
                "Offers.Listings.SavingBasis",
                "Offers.Listings.Availability.Message",
                "CustomerReviews.Count",
                "CustomerReviews.StarRating"
            ],
            "PartnerTag": settings.AMAZON_PAAPI_TAG,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.in",
            "ItemCount": min(limit, 10)
        }
        
        payload_str = json.dumps(payload)
        now = datetime.now(timezone.utc)
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')

        canonical_uri = '/paapi5/searchitems'
        canonical_querystring = ''
        canonical_headers = f'content-encoding:amz-1.0\ncontent-type:application/json; charset=utf-8\nhost:{self.host}\nx-amz-date:{amz_date}\nx-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems\n'
        signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        canonical_request = f'POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'

        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f'{date_stamp}/{self.region}/{self.service}/aws4_request'
        string_to_sign = f'{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'

        signing_key = self._get_signature_key(settings.AMAZON_PAAPI_SECRET_KEY, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        authorization_header = f'{algorithm} Credential={settings.AMAZON_PAAPI_ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'

        headers = {
            'content-encoding': 'amz-1.0',
            'content-type': 'application/json; charset=utf-8',
            'x-amz-date': amz_date,
            'x-amz-target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
            'Authorization': authorization_header,
            'host': self.host
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.endpoint, headers=headers, content=payload_str)
                self._last_latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("SearchResult", {}).get("Items", [])
                    products = []
                    
                    for it in items:
                        asin = it.get("ASIN", "")
                        detail_url = it.get("DetailPageURL", f"https://www.amazon.in/dp/{asin}")
                        item_info = it.get("ItemInfo", {})
                        title = item_info.get("Title", {}).get("DisplayValue", "")
                        by_line = item_info.get("ByLineInfo", {})
                        brand = by_line.get("Brand", {}).get("DisplayValue", "Generic")
                        
                        # Features
                        features_list = [f.get("DisplayValue", "") for f in item_info.get("Features", {}).get("DisplayValues", [])]
                        
                        # Images
                        image_url = it.get("Images", {}).get("Primary", {}).get("Large", {}).get("URL", "")
                        
                        # Price
                        offers = it.get("Offers", {}).get("Listings", [])
                        current_price = None
                        original_price = None
                        discount = None
                        avail = "In Stock"
                        seller_name = "Amazon India Verified"
                        
                        if offers:
                            listing = offers[0]
                            price_obj = listing.get("Price", {})
                            if "Amount" in price_obj:
                                current_price = float(price_obj.get("Amount", 0.0))
                            saving_basis = listing.get("SavingBasis", {})
                            if saving_basis and "Amount" in saving_basis:
                                original_price = float(saving_basis.get("Amount", 0.0))
                                if current_price and original_price > current_price > 0:
                                    discount = round(((original_price - current_price) / original_price) * 100, 1)
                            avail = listing.get("Availability", {}).get("Message", "In Stock")
                            if "MerchantInfo" in listing:
                                seller_name = listing.get("MerchantInfo", {}).get("Name", seller_name)

                        # Customer Reviews
                        reviews = it.get("CustomerReviews", {})
                        rating = float(reviews.get("StarRating", {}).get("Value")) if reviews.get("StarRating") else None
                        review_count = int(reviews.get("Count")) if reviews.get("Count") else None
                        
                        norm_prod = NormalizedProduct(
                            id=f"amzn_{asin}",
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
                            availability=avail,
                            product_url=detail_url,
                            marketplace="Amazon India",
                            provider=self.provider_id,
                            seller=seller_name,
                            source="Amazon India Official PA-API 5.0",
                            specifications={"ASIN": asin, "Brand": brand},
                            features=features_list,
                            offers=[
                                MarketplaceOffer(
                                    marketplace="Amazon India",
                                    provider=self.provider_id,
                                    product_url=detail_url,
                                    current_price=current_price,
                                    original_price=original_price,
                                    discount_percent=discount,
                                    currency="INR",
                                    in_stock=True,
                                    rating=rating,
                                    review_count=review_count,
                                    seller_name=seller_name
                                )
                            ]
                        )
                        products.append(norm_prod)
                        
                    self._last_items_count = len(products)
                    self._last_status = "active"
                    self._last_message = f"Successfully fetched {len(products)} live products from Amazon India PA-API."
                    return products
                else:
                    self._last_status = "error"
                    self._last_message = f"Amazon PA-API returned HTTP {resp.status_code}: {resp.text[:150]}"
                    return []
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Error connecting to Amazon PA-API: {str(e)}"
            return []


class AmazonCreatorsAPIProvider(BaseProductProvider):
    """
    Amazon India Creators API provider.
    """
    def __init__(self):
        super().__init__(
            provider_id="amazon_creators_india",
            name="Amazon India Creators API",
            marketplace="Amazon India",
        )
        self.endpoint = "https://creatorsapi.amazon/catalog/v1/searchItems"
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0
        self.is_optional = True

    def is_configured(self) -> bool:
        return bool(
            getattr(settings, "AMAZON_CREATORS_CREDENTIAL_ID", None)
            and getattr(settings, "AMAZON_CREATORS_CREDENTIAL_SECRET", None)
            and getattr(settings, "AMAZON_CREATORS_CREDENTIAL_VERSION", None)
            and getattr(settings, "AMAZON_CREATORS_PARTNER_TAG", None)
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

        token_endpoint = getattr(settings, "AMAZON_CREATORS_TOKEN_ENDPOINT", "https://api.amazon.com/auth/o2/token")
        response = await client.post(
            token_endpoint,
            headers={"Content-Type": "application/json"},
            json={
                "grant_type": "client_credentials",
                "client_id": getattr(settings, "AMAZON_CREATORS_CREDENTIAL_ID", ""),
                "client_secret": getattr(settings, "AMAZON_CREATORS_CREDENTIAL_SECRET", ""),
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

    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        start_time = time.time()
        if not self.is_configured():
            self._last_status = "optional / unavailable"
            self._last_message = "Amazon Creators API requires Credential ID, Credential Secret, Version, and Partner Tag."
            self._last_items_count = 0
            self._last_latency_ms = (time.time() - start_time) * 1000
            return []

        payload = {
            "keywords": query,
            "partnerTag": getattr(settings, "AMAZON_CREATORS_PARTNER_TAG", ""),
            "marketplace": "www.amazon.in",
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
                items = data.get("itemsResult", {}).get("items", [])
                products: List[NormalizedProduct] = []
                for item in items:
                    asin = item.get("asin", "")
                    item_info = item.get("itemInfo", {})
                    title = item_info.get("title", {}).get("displayValue", "")
                    detail_url = item.get("detailPageURL", f"https://www.amazon.in/dp/{asin}")
                    brand = item_info.get("byLineInfo", {}).get("brand", {}).get("displayValue", "Generic")
                    
                    images = item.get("images", {}).get("primary", {})
                    image_url = ""
                    for sz in ("hiRes", "large", "medium", "small"):
                        if sz in images and "url" in images[sz]:
                            image_url = images[sz]["url"]
                            break
                            
                    reviews = item.get("customerReviews", {})
                    rating = float(reviews.get("starRating", {}).get("value")) if reviews.get("starRating") else None
                    review_count = int(reviews.get("count")) if reviews.get("count") else None
                    
                    offers_v2 = item.get("offersV2", {}).get("listings", [])
                    current_price = None
                    avail = "Unknown"
                    if offers_v2:
                        listing = offers_v2[0]
                        price_obj = listing.get("price", {})
                        if "amount" in price_obj:
                            current_price = float(price_obj["amount"])
                        avail = listing.get("availability", {}).get("message") or "Unknown"

                    norm_prod = NormalizedProduct(
                        id=f"amzn_creator_{asin}",
                        source_product_id=asin or None,
                        title=title,
                        brand=brand,
                        category=category,
                        image_url=image_url,
                        current_price=current_price,
                        original_price=None,
                        discount_percent=None,
                        currency="INR",
                        rating=rating,
                        review_count=review_count,
                        availability=avail,
                        product_url=detail_url,
                        marketplace="Amazon India",
                        provider=self.provider_id,
                        seller=None,
                        source="Amazon India Creators API",
                        specifications={"ASIN": asin, "Brand": brand} if asin else {},
                        features=[f"Amazon India Listing • ASIN: {asin}"] if asin else [],
                        offers=[
                            MarketplaceOffer(
                                marketplace="Amazon India",
                                provider=self.provider_id,
                                product_url=detail_url,
                                current_price=current_price,
                                original_price=None,
                                discount_percent=None,
                                currency="INR",
                                in_stock=True if avail == "In Stock" else None,
                                rating=rating,
                                review_count=review_count,
                                seller_name=None
                            )
                        ]
                    )
                    products.append(norm_prod)

                self._last_items_count = len(products)
                self._last_status = "active"
                return products
        except Exception as e:
            self._last_latency_ms = (time.time() - start_time) * 1000
            self._last_status = "unavailable"
            self._last_message = f"Error in Amazon Creators API: {str(e)}"
            return []

