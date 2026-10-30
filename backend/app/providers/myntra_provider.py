import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

import httpx
import requests

from app.core.config import settings
from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.providers.base import BaseProductProvider
from app.services.brightdata_service import (
    BrightDataServiceError,
    fetch_myntra_products,
)
from app.services.normalization_service import NormalizationService


logger = logging.getLogger(__name__)


# Categories carried by Myntra
MYNTRA_SUPPORTED_CATEGORIES = {
    "dress",
    "shoes",
    "fashion",
    "apparel",
    "clothing",
    "tshirt",
    "shirt",
    "jeans",
    "kurti",
    "watches",
    "smartwatch",
    "headphones",
    "accessories",
    "beauty",
    "skincare",
    "hair_care",
    "makeup",
    "bags",
    "general",
}


# Categories that Myntra does not normally carry
MYNTRA_EXCLUDED_CATEGORIES = {
    "laptop",
    "tv",
    "refrigerator",
    "washing_machine",
    "ac",
    "camera",
}


def _clean_number(value: Any) -> Optional[float]:
    """
    Convert different price/rating formats into a number.

    Examples:
        "₹1,299" -> 1299.0
        "1299" -> 1299.0
        "4.5" -> 4.5
        {"amount": 1299} -> 1299.0
        {"discounted": 389} -> 389.0
    """

    if value is None or isinstance(value, bool):
        return None

    # Handle dictionary values
    if isinstance(value, dict):
        value = (
            value.get("amount")
            or value.get("value")
            or value.get("discounted")
            or value.get("price")
            or value.get("mrp")
            or value.get("averageRating")
            or value.get("totalCount")
        )

    # Handle integer / float
    if isinstance(value, (int, float)):
        return float(value)

    # Handle string
    if not isinstance(value, str):
        return None

    # Extract number from strings such as ₹1,299 or "4.5"
    match = re.search(r"\d[\d,]*(?:\.\d+)?", value)

    if match:
        return float(match.group(0).replace(",", ""))

    return None


class MyntraProvider(BaseProductProvider):
    """
    Myntra Fashion & Lifestyle Marketplace Provider.

    Discovers fashion, beauty, footwear, and lifestyle products
    on Myntra India.

    Product data is fetched through Bright Data's Myntra dataset.
    """

    def __init__(self):
        super().__init__(
            provider_id="myntra_fashion",
            name="Myntra Fashion & Lifestyle",
            marketplace="Myntra",
        )

        self.endpoint = "https://serpapi.com/search"

        # Myntra catalog limitation:
        #
        # Myntra mainly carries:
        # - Fashion
        # - Footwear
        # - Beauty
        # - Accessories
        # - Lifestyle products
        #
        # It does not normally carry:
        # - Laptops
        # - TVs
        # - Refrigerators
        # - Washing machines
        # - AC
        # - Cameras

        self._last_message = (
            "Myntra catalog ready "
            "(fashion, footwear & beauty via Bright Data; "
            "electronics/laptops not carried)."
        )

    def is_configured(self) -> bool:
        """
        Check whether Myntra provider is properly configured.
        """

        if not settings.ENABLE_MYNTRA_PROVIDER:
            return False

        key = os.getenv("BRIGHTDATA_API_KEY", "").strip()

        return bool(key) and not key.upper().startswith(
            ("YOUR_", "REPLACE_", "<")
        )

    def is_enabled(self) -> bool:
        """
        Check whether Myntra provider is enabled.
        """

        return settings.ENABLE_MYNTRA_PROVIDER

    def get_required_env_keys(self) -> List[str]:
        """
        Return required environment variables.
        """

        if not self.is_configured():
            return ["BRIGHTDATA_API_KEY"]

        return []

    @classmethod
    def _extract_rating_and_reviews(cls, record: Dict[str, Any]) -> Tuple[Optional[float], Optional[int]]:
        """Safely extract authentic star rating and review/rating count across all Myntra record variants."""
        rating: Optional[float] = None
        review_count: Optional[int] = None

        # 1. Check nested ratings dictionary (e.g. ratings: {"averageRating": 4.3, "totalCount": 1520})
        ratings_obj = record.get("ratings")
        if isinstance(ratings_obj, dict):
            r_avg = _clean_number(
                ratings_obj.get("averageRating") or ratings_obj.get("rating") or ratings_obj.get("avg_rating") or ratings_obj.get("stars") or ratings_obj.get("value")
            )
            r_cnt = _clean_number(
                ratings_obj.get("totalCount") or ratings_obj.get("ratingCount") or ratings_obj.get("reviewCount") or ratings_obj.get("count") or ratings_obj.get("ratingsCount") or ratings_obj.get("reviewsCount")
            )
            if r_avg is not None:
                rating = r_avg
            if r_cnt is not None:
                review_count = int(r_cnt)

        # 2. Check flat rating fields if not yet found
        if rating is None:
            for r_key in [
                "rating", "star_rating", "stars", "rating_value",
                "average_customer_review", "average_rating", "avg_rating",
                "averageRating", "product_rating", "user_rating"
            ]:
                if r_key in record and not isinstance(record[r_key], (dict, list)):
                    val = _clean_number(record[r_key])
                    if val is not None and 0 < val <= 5.0:
                        rating = val
                        break

        # 3. Check flat review / rating count fields if not yet found
        if review_count is None:
            for c_key in [
                "reviews_count", "review_count", "num_reviews", "number_of_reviews",
                "total_reviews", "ratingCount", "ratings_count", "rating_count",
                "num_ratings", "total_ratings", "totalCount", "count"
            ]:
                if c_key in record and not isinstance(record[c_key], (dict, list)):
                    cnt = _clean_number(record[c_key])
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
    def normalize_record(
        cls,
        record: Dict[str, Any],
        category: str,
    ) -> Optional[NormalizedProduct]:
        """
        Normalize a raw Bright Data Myntra record
        into NormalizedProduct.
        """

        # ---------------------------------------------------------
        # PRODUCT URL
        # ---------------------------------------------------------

        product_url = record.get("url") or record.get("link") or record.get("product_url")
        landing_page = record.get("landingPageUrl")
        if not product_url and landing_page:
            if str(landing_page).startswith("http"):
                product_url = str(landing_page)
            else:
                product_url = f"https://www.myntra.com/{str(landing_page).lstrip('/')}"

        if not product_url:
            return None

        if not NormalizationService.is_direct_product_url(
            product_url,
            "Myntra",
        ):
            return None

        clean_url = (
            NormalizationService.unwrap_product_url(product_url)
            or product_url
        )

        # ---------------------------------------------------------
        # PRODUCT ID
        # ---------------------------------------------------------

        item_id = str(
            record.get("productId")
            or record.get("product_id")
            or record.get("id")
            or ""
        )

        if not item_id:
            match = re.search(
                r"/(\d+)(?:/buy)?$",
                clean_url,
            )

            item_id = (
                match.group(1)
                if match
                else clean_url
            )

        # ---------------------------------------------------------
        # BRAND + PRODUCT TITLE
        # ---------------------------------------------------------

        # ---------------------------------------------------------
        # BRAND + PRODUCT TITLE
        # ---------------------------------------------------------

        brand_val = (
            record.get("brand")
            or record.get("brandName")
            or record.get("title")
            or ""
        )
        if isinstance(brand_val, dict):
            brand_raw = str(brand_val.get("name") or brand_val.get("brandName") or "").strip()
        else:
            brand_raw = str(brand_val).strip()

        desc_val = (
            record.get("product")
            or record.get("productName")
            or record.get("product_description")
            or record.get("name")
            or ""
        )
        if isinstance(desc_val, dict):
            desc_raw = str(desc_val.get("name") or desc_val.get("title") or "").strip()
        else:
            desc_raw = str(desc_val).strip()

        if brand_raw and desc_raw:
            if desc_raw.lower().startswith(brand_raw.lower()):
                title = desc_raw
            else:
                title = f"{brand_raw} {desc_raw}"
            brand = brand_raw
        elif desc_raw:
            title = desc_raw
            brand = "Unknown"
        elif brand_raw:
            title = brand_raw
            brand = brand_raw
        else:
            return None

        # ---------------------------------------------------------
        # PRICE
        # ---------------------------------------------------------

        price_obj = record.get("price")
        if isinstance(price_obj, dict):
            current_price = _clean_number(
                price_obj.get("discounted")
                or price_obj.get("final_price")
                or price_obj.get("sale_price")
                or price_obj.get("price")
            )
            original_price = _clean_number(
                price_obj.get("mrp")
                or price_obj.get("initial_price")
                or price_obj.get("original_price")
            )
        else:
            current_price = _clean_number(
                record.get(
                    "final_price",
                    record.get(
                        "sale_price",
                        record.get(
                            "current_price",
                            record.get(
                                "price_value",
                                record.get(
                                    "deal_price",
                                    record.get(
                                        "offer_price",
                                        record.get(
                                            "price",
                                            record.get("extracted_price"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
            )

            original_price = _clean_number(
                record.get(
                    "initial_price",
                    record.get(
                        "original_price",
                        record.get(
                            "list_price",
                            record.get(
                                "was_price",
                                record.get(
                                    "mrp",
                                    record.get(
                                        "regular_price",
                                        record.get("extracted_old_price"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
            )

        # If only original price exists, treat it as current price
        if current_price is None and original_price is not None:
            current_price = original_price
            original_price = None
        elif current_price is not None and original_price is not None and original_price <= current_price:
            original_price = None

        # ---------------------------------------------------------
        # DISCOUNT
        # ---------------------------------------------------------

        discount = _clean_number(
            record.get("discount") or record.get("discount_percent")
        )

        if not discount and current_price and original_price and original_price > current_price:
            discount = round(
                (((original_price - current_price) / original_price) * 100),
                1,
            )

        # ---------------------------------------------------------
        # RATING & REVIEWS
        # ---------------------------------------------------------

        rating, review_count = cls._extract_rating_and_reviews(record)

        # ---------------------------------------------------------
        # IMAGES
        # ---------------------------------------------------------

        image_candidates: List[str] = []

        def _clean_img_url(img_str: str) -> str:
            if not isinstance(img_str, str) or not (img_str.startswith("http://") or img_str.startswith("https://")):
                return ""
            if "($height)" in img_str or "($width)" in img_str:
                img_str = img_str.replace("($height)", "720").replace("($width)", "540").replace("($qualityPercentage)", "90")
            return img_str.strip()

        def _collect_img(val: Any):
            if not val:
                return
            if isinstance(val, str):
                cleaned = _clean_img_url(val)
                if cleaned and cleaned not in image_candidates:
                    image_candidates.append(cleaned)
            elif isinstance(val, list):
                for x in val:
                    _collect_img(x)
            elif isinstance(val, dict):
                for k in ("imageURL", "image_url", "searchImage", "primary_image", "main_image", "image", "thumbnail", "secureSrc", "src"):
                    if k in val and isinstance(val[k], str):
                        _collect_img(val[k])
                for v in val.values():
                    if isinstance(v, (list, dict)):
                        _collect_img(v)

        _collect_img(record.get("media"))
        _collect_img(record.get("searchImage"))
        _collect_img(record.get("images"))
        _collect_img(record.get("image_urls"))
        _collect_img(record.get("additional_image_urls"))
        _collect_img(record.get("additional_images"))
        _collect_img(record.get("primary_image"))
        _collect_img(record.get("main_image"))
        _collect_img(record.get("image_url"))
        _collect_img(record.get("image_link"))
        _collect_img(record.get("image"))
        _collect_img(record.get("thumbnail"))

        image_url = image_candidates[0] if image_candidates else ""

        # ---------------------------------------------------------
        # REVIEWS
        # ---------------------------------------------------------

        pdp_reviews = record.get("reviews")
        if isinstance(pdp_reviews, dict):
            rev_list = pdp_reviews.get("reviews") or pdp_reviews.get("customerReviews") or []
            if isinstance(rev_list, list) and rev_list:
                valid_revs = []
                for r in rev_list:
                    if isinstance(r, dict):
                        text = r.get("reviewText") or r.get("text") or r.get("review") or r.get("userReview")
                        if text:
                            valid_revs.append({
                                "review_text": text,
                                "rating": r.get("userRating") or r.get("rating"),
                                "title": r.get("headline") or r.get("title") or "",
                                "reviewer_name": r.get("userName") or r.get("author") or "Verified Buyer",
                                "verified_purchase": True,
                            })
                if valid_revs and "written_reviews" not in record:
                    record["written_reviews"] = valid_revs
        elif isinstance(pdp_reviews, list) and pdp_reviews:
            valid_revs = [r for r in pdp_reviews if isinstance(r, dict)]
            if valid_revs and "written_reviews" not in record:
                record["written_reviews"] = valid_revs

        raw_reviews = record.get("customer_reviews")
        if isinstance(raw_reviews, list) and raw_reviews:
            valid_revs = [r for r in raw_reviews if isinstance(r, dict)]
            if valid_revs and "written_reviews" not in record:
                record["written_reviews"] = valid_revs

        # ---------------------------------------------------------
        # SPECIFICATIONS
        # ---------------------------------------------------------

        specs: Dict[str, str] = {}

        prod_details = record.get("productDetails")
        if isinstance(prod_details, list):
            for detail in prod_details:
                if isinstance(detail, dict):
                    t = detail.get("title")
                    desc = detail.get("description")
                    if t and desc:
                        specs[str(t).strip()] = str(desc).strip()

        raw_specs = record.get("product_specifications")
        if isinstance(raw_specs, list):
            for entry in raw_specs:
                if not isinstance(entry, dict):
                    continue
                key = entry.get("specification_name") or entry.get("key") or entry.get("name")
                value = entry.get("specification_value") or entry.get("value")
                if key and value and str(value).strip() not in ("NA", "None", ""):
                    specs[str(key).strip()] = str(value).strip()
        elif isinstance(raw_specs, dict):
            specs.update(
                {str(k): str(v) for k, v in raw_specs.items() if v not in (None, "")}
            )

        if brand and brand != "Unknown" and "Brand" not in specs:
            specs["Brand"] = brand

        # ---------------------------------------------------------
        # CUSTOMER SENTIMENT / HIGHLIGHTS
        # ---------------------------------------------------------

        features = []

        what_customers_said = record.get(
            "what_customers_said"
        )

        if isinstance(
            what_customers_said,
            list,
        ):

            for item in what_customers_said:

                if not isinstance(item, dict):
                    continue

                value_name = item.get(
                    "value_name"
                )

                if not value_name:
                    continue

                percentage = item.get(
                    "percentage"
                )

                if percentage:
                    features.append(
                        f"{value_name} "
                        f"({percentage}% positive)"
                    )
                else:
                    features.append(
                        str(value_name)
                    )

        # ---------------------------------------------------------
        # AVAILABILITY
        # ---------------------------------------------------------

        availability = (
            record.get("availability")
            or "Unknown"
        )

        # ---------------------------------------------------------
        # CREATE NORMALIZED PRODUCT
        # ---------------------------------------------------------

        product = NormalizedProduct(
            id=f"myntra_{item_id}",

            source_product_id=str(
                item_id
            ),

            title=title.strip(),

            brand=brand,

            category=category,

            image_url=image_url,

            current_price=current_price,

            original_price=original_price,

            discount_percent=discount,

            currency="INR",

            rating=rating,

            review_count=review_count,

            availability=availability,

            product_url=clean_url,

            marketplace="Myntra",

            provider="myntra_fashion",

            seller=(
                record.get("seller_name")
                or "Myntra"
            ),

            source=(
                "Bright Data Myntra Dataset "
                "(gd_lptvxr8b1qx1d9thgp)"
            ),

            specifications=specs,

            features=features,

            image_candidates=image_candidates,

            raw_data=record,

            offers=[
                MarketplaceOffer(
                    marketplace="Myntra",

                    provider="myntra_fashion",

                    product_url=clean_url,

                    current_price=current_price,

                    original_price=original_price,

                    discount_percent=discount,

                    currency="INR",

                    in_stock=(
                        True
                        if availability == "In Stock"
                        else None
                    ),

                    rating=rating,

                    review_count=review_count,

                    seller_name=(
                        record.get("seller_name")
                        or "Myntra"
                    ),
                )
            ],
        )

        # ---------------------------------------------------------
        # FINAL NORMALIZATION
        # ---------------------------------------------------------

        return NormalizationService.normalize_product(
            product
        )

    def _fetch_direct_catalog_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Query live Myntra catalog index for products matching the query synchronously.
        """
        import urllib.parse
        encoded = urllib.parse.quote(query.strip())
        url = f"https://www.myntra.com/{encoded}?rawQuery={encoded}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;"
                "q=0.9,*/*;"
                "q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            from json import JSONDecoder
            decoder = JSONDecoder()
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                scripts = re.findall(r"<script[^>]*>(.*?)</script>", resp.text, re.DOTALL)
                for s in scripts:
                    if "window.__myx" in s and "{" in s:
                        idx = s.find("{")
                        if idx != -1:
                            try:
                                data, _ = decoder.raw_decode(s[idx:])
                                products = data.get("searchData", {}).get("results", {}).get("products", [])
                                if isinstance(products, list) and products:
                                    return products[:limit]
                            except Exception:
                                pass
        except Exception as exc:
            logger.warning("Live Myntra catalog query failed: %s", exc)
        return []

    async def _search_direct_catalog(
        self,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Query live Myntra catalog index for products matching the query asynchronously.
        """
        return await asyncio.to_thread(self._fetch_direct_catalog_sync, query, limit)

    async def _search_direct_web(
        self,
        query: str,
        limit: int,
    ) -> List[str]:
        """
        Discover live direct Myntra product URLs
        from catalog and search indexes.
        """
        catalog_products = await self._search_direct_catalog(query, limit)
        urls = []
        for p in catalog_products:
            landing = p.get("landingPageUrl")
            if landing:
                u = str(landing) if str(landing).startswith("http") else f"https://www.myntra.com/{str(landing).lstrip('/')}"
                if NormalizationService.is_direct_product_url(u, "Myntra") and u not in urls:
                    urls.append(u)

        if len(urls) >= limit:
            return urls[:limit]

        return urls

    async def search(
        self,
        query: str,
        category: str,
        limit: int = 10,
    ) -> List[NormalizedProduct]:

        started = time.time()

        # ---------------------------------------------------------
        # CATEGORY CHECK
        # ---------------------------------------------------------

        if category in MYNTRA_EXCLUDED_CATEGORIES:
            self._last_status = "idle"
            self._last_message = (
                "Skipped: Myntra is an apparel "
                "& lifestyle marketplace and "
                f"does not carry products for "
                f"category '{category}'."
            )
            self._last_items_count = 0
            self._last_latency_ms = (time.time() - started) * 1000
            return []

        # ---------------------------------------------------------
        # API CONFIGURATION CHECK
        # ---------------------------------------------------------

        if not self.is_configured():
            self._last_status = "credentials_required"
            self._last_message = (
                "Live product data is currently "
                "unavailable for Myntra. "
                "Configure BRIGHTDATA_API_KEY."
            )
            self._last_items_count = 0
            self._last_latency_ms = (time.time() - started) * 1000
            return []

        # ---------------------------------------------------------
        # FETCH PRODUCTS
        # ---------------------------------------------------------

        try:
            discovered_urls = await self._search_direct_web(query, limit)
            discovered_urls = list(dict.fromkeys(discovered_urls))

            if not discovered_urls:
                self._last_latency_ms = (time.time() - started) * 1000
                self._last_items_count = 0
                self._last_status = "empty"
                self._last_message = "Live product data is currently unavailable for Myntra."
                return []

            records = await asyncio.to_thread(
                fetch_myntra_products,
                discovered_urls[:limit],
            )

            # If dataset returns empty, use the direct catalog records discovered for this query
            if not records:
                catalog_records = await self._search_direct_catalog(query, limit)
                if catalog_records:
                    records = catalog_records

            products = []
            seen_ids = set()

            for record in records:
                product = self.normalize_record(record, category)
                if product and product.id not in seen_ids:
                    seen_ids.add(product.id)
                    products.append(product)

            # -------------------------------------------------
            # STATUS
            # -------------------------------------------------

            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = len(products)
            self._last_status = "active" if products else "empty"

            if products:
                self._last_message = (
                    f"Fetched {len(products)} live Myntra products via Bright Data."
                )
            else:
                self._last_message = "Live product data is currently unavailable for Myntra."

            return products

        except BrightDataServiceError as exc:
            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = 0
            self._last_status = "unavailable"
            self._last_message = (
                f"Live product data is currently unavailable for Myntra: {exc}"
            )
            logger.warning("Bright Data Myntra error: %s", exc)
            return []

        except Exception as exc:
            self._last_latency_ms = (time.time() - started) * 1000
            self._last_items_count = 0
            self._last_status = "unavailable"
            self._last_message = "Live product data is currently unavailable for Myntra."
            logger.exception("Unexpected Myntra provider error: %s", exc)
            return []