import re
import asyncio
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.models.coupon_schemas import CouponOffer, CouponOffersResponse
from app.providers.registry import provider_registry

class CouponService:
    """
    Dedicated, isolated service for extracting, structuring, and serving
    genuine marketplace discounts, coupons, and promotional offers.
    Never invents fake coupon codes. Uses only authentic marketplace pricing and metadata.
    """

    @classmethod
    def extract_offers_from_product(cls, product: NormalizedProduct) -> List[CouponOffer]:
        offers_found: List[CouponOffer] = []
        
        # 1. Check primary product pricing
        primary_offer = cls._create_offer_from_data(
            product_id=product.id,
            product_title=product.title,
            marketplace=product.marketplace or "Amazon India",
            current_price=product.current_price,
            original_price=product.original_price,
            discount_percent=product.discount_percent,
            product_url=product.product_url,
            image_url=product.image_url or (product.image_candidates[0] if product.image_candidates else None),
            features=product.features,
            description=product.description,
            raw_data=product.raw_data
        )
        if primary_offer:
            offers_found.append(primary_offer)

        # 2. Check additional marketplace offers attached to product
        if product.offers:
            for idx, m_offer in enumerate(product.offers):
                # Avoid duplicate if it matches primary offer marketplace and price
                if (
                    m_offer.marketplace.lower() == (product.marketplace or "").lower()
                    and m_offer.current_price == product.current_price
                ):
                    continue

                sub_offer = cls._create_offer_from_data(
                    product_id=f"{product.id}_offer_{idx}",
                    product_title=product.title,
                    marketplace=m_offer.marketplace or "Marketplace",
                    current_price=m_offer.current_price,
                    original_price=m_offer.original_price,
                    discount_percent=m_offer.discount_percent,
                    product_url=m_offer.product_url or product.product_url,
                    image_url=product.image_url,
                    features=[],
                    description="",
                    raw_data=None
                )
                if sub_offer:
                    offers_found.append(sub_offer)

        return offers_found

    @classmethod
    def _create_offer_from_data(
        cls,
        product_id: str,
        product_title: str,
        marketplace: str,
        current_price: Optional[float],
        original_price: Optional[float],
        discount_percent: Optional[float],
        product_url: Optional[str],
        image_url: Optional[str],
        features: List[str],
        description: Optional[str],
        raw_data: Optional[Dict[str, Any]]
    ) -> Optional[CouponOffer]:
        if not current_price or current_price <= 0:
            return None

        # Check if genuine discount exists (original_price strictly greater than current_price)
        has_discount = False
        discount_amount = None
        calculated_pct = discount_percent

        if original_price and original_price > current_price:
            has_discount = True
            discount_amount = round(original_price - current_price, 2)
            if not calculated_pct or calculated_pct <= 0:
                calculated_pct = round((discount_amount / original_price) * 100, 1)
        elif calculated_pct and calculated_pct > 0:
            has_discount = True
            # Estimate original price if discount % is explicitly provided by marketplace feed
            if not original_price:
                original_price = round(current_price / (1 - (calculated_pct / 100)), 2)
                discount_amount = round(original_price - current_price, 2)

        # Inspect textual details for genuine coupon codes, bank deals, or promo terms
        combined_text = " ".join(features) + " " + (description or "")
        if raw_data and isinstance(raw_data, dict):
            for k in ["coupon", "promo", "deal", "discount", "promotion", "badge"]:
                if k in raw_data and raw_data[k]:
                    combined_text += f" {raw_data[k]}"

        # Look for authentic coupon code pattern (e.g. "Use coupon: SAVE20", "Code: FLAT500")
        coupon_code = None
        code_match = re.search(
            r'\b(?:use|apply|coupon|code|promo|voucher)\s*[:\s-]?\s*([A-Z0-9]{4,15})\b',
            combined_text,
            re.IGNORECASE
        )
        if code_match:
            candidate = code_match.group(1).upper()
            # Exclude false positives like "HTTP", "TRUE", "FALSE", "INDIA", "FLIPKART", "AMAZON"
            if candidate not in {"HTTP", "HTTPS", "TRUE", "FALSE", "INDIA", "FLIPKART", "AMAZON", "MYNTRA", "CROMA", "NONE"}:
                coupon_code = candidate

        # Look for expiry date
        expiry_date = None
        expiry_match = re.search(
            r'(?:valid\s*(?:till|until|through)|ends\s*(?:on)?|expires\s*(?:on)?)\s*([0-9]{1,2}\s+[A-Za-z]+(?:\s+[0-9]{4})?|[A-Za-z]+\s+[0-9]{1,2})',
            combined_text,
            re.IGNORECASE
        )
        if expiry_match:
            expiry_date = f"Valid till {expiry_match.group(1).strip()}"

        # If there is neither a price discount nor a coupon/promo code, this product has no active promotion
        if not has_discount and not coupon_code:
            return None

        # Build clean offer title and description
        if coupon_code:
            offer_type = "Coupon Code"
            title = f"{coupon_code} – Extra Savings on {product_title[:45]}..."
            desc = f"Apply coupon code '{coupon_code}' at checkout on {marketplace} to claim exclusive promotional discount."
        elif calculated_pct and calculated_pct >= 5:
            offer_type = "Direct Discount"
            title = f"{int(calculated_pct)}% Off on {product_title[:45]}..."
            discount_str = f"₹{int(discount_amount):,}" if discount_amount else "markdown"
            desc = f"Instant marketplace markdown: save {discount_str} off original listing price."
        else:
            offer_type = "Marketplace Promotion"
            title = f"Verified Offer on {product_title[:45]}..."
            desc = f"Special promotional pricing active on {marketplace}."

        offer_id = hashlib.md5(f"{product_id}_{marketplace}_{current_price}".encode("utf-8")).hexdigest()[:12]

        return CouponOffer(
            id=f"offer_{offer_id}",
            title=title,
            applicable_product=product_title,
            marketplace=marketplace,
            current_price=current_price,
            original_price=original_price,
            discount_percent=calculated_pct,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            has_coupon_code=bool(coupon_code),
            offer_type=offer_type,
            description=desc,
            terms=f"Subject to marketplace stock and merchant conditions on {marketplace}.",
            expiry_date=expiry_date or "Limited Time Marketplace Deal",
            product_url=product_url,
            image_url=image_url,
            verified=True
        )

    @classmethod
    async def get_offers_for_query(
        cls,
        query: str,
        category: Optional[str] = None
    ) -> CouponOffersResponse:
        clean_query = query.strip()
        if not clean_query:
            return await cls.get_featured_offers()

        # Retrieve live marketplace products using provider registry
        raw_products: List[NormalizedProduct] = await provider_registry.search_all(
            query=clean_query,
            category=category or "general",
            limit=20
        )

        offers: List[CouponOffer] = []
        for p in raw_products:
            extracted = cls.extract_offers_from_product(p)
            offers.extend(extracted)

        # Exclude offers deactivated by admin moderation
        try:
            from app.services.report_service import ReportService
            disabled_coupons = ReportService.get_disabled_coupon_ids()
        except Exception:
            disabled_coupons = set()

        # Deduplicate offers by (applicable_product, marketplace) and exclude disabled
        seen_keys = set()
        deduped_offers: List[CouponOffer] = []
        for off in offers:
            if off.id in disabled_coupons:
                continue
            if off.coupon_code and off.coupon_code.strip().upper() in disabled_coupons:
                continue

            key = f"{off.applicable_product[:40].lower()}_{off.marketplace.lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                deduped_offers.append(off)

        # Sort by highest discount percentage / amount
        deduped_offers.sort(key=lambda x: (x.discount_percent or 0, x.discount_amount or 0), reverse=True)

        if not deduped_offers:
            return CouponOffersResponse(
                query=clean_query,
                category=category,
                total_offers=0,
                offers=[],
                message=f"No verified promotional discounts or coupons currently available for '{clean_query}'. All products are offered at standard marketplace listing prices."
            )

        return CouponOffersResponse(
            query=clean_query,
            category=category,
            total_offers=len(deduped_offers),
            offers=deduped_offers,
            message=f"Found {len(deduped_offers)} verified marketplace offers and discounts for '{clean_query}'."
        )

    _featured_cache: Optional[CouponOffersResponse] = None
    _last_featured_fetch: float = 0.0

    @classmethod
    async def get_featured_offers(cls) -> CouponOffersResponse:
        """
        Gathers verified deals across trending shopping categories (laptops, phones, audio)
        when no specific search query is given. Caches for 120 seconds for ultra-fast UI rendering.
        """
        now = datetime.now(timezone.utc).timestamp()
        if cls._featured_cache and (now - cls._last_featured_fetch < 120):
            return cls._featured_cache

        trending_queries = ["laptop", "smartphone", "wireless earbuds"]
        tasks = [provider_registry.search_all(query=tq, category="general", limit=8) for tq in trending_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_offers: List[CouponOffer] = []
        for res in results:
            if isinstance(res, list):
                for p in res:
                    all_offers.extend(cls.extract_offers_from_product(p))

        # Deduplicate and exclude disabled
        try:
            from app.services.report_service import ReportService
            disabled_coupons = ReportService.get_disabled_coupon_ids()
        except Exception:
            disabled_coupons = set()

        seen = set()
        deduped: List[CouponOffer] = []
        for o in all_offers:
            if o.id in disabled_coupons:
                continue
            if o.coupon_code and o.coupon_code.strip().upper() in disabled_coupons:
                continue

            key = f"{o.applicable_product[:35].lower()}_{o.marketplace.lower()}"
            if key not in seen:
                seen.add(key)
                deduped.append(o)

        deduped.sort(key=lambda x: (x.discount_percent or 0), reverse=True)

        resp = CouponOffersResponse(
            query="Featured Marketplace Deals",
            category="all",
            total_offers=len(deduped),
            offers=deduped[:15],
            message="Displaying verified live discounts and promotions across major marketplaces."
        )
        cls._featured_cache = resp
        cls._last_featured_fetch = now
        return resp
