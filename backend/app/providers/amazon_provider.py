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
