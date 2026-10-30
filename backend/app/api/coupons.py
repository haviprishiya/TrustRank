import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Body
from app.models.coupon_schemas import CouponOffer, CouponOffersResponse
from app.services.coupon_service import CouponService
from app.models.schemas import NormalizedProduct

router = APIRouter(prefix="/coupons", tags=["Coupons & Offers"])
logger = logging.getLogger(__name__)

@router.get("/offers", response_model=CouponOffersResponse)
async def get_coupon_offers(
    query: Optional[str] = Query(None, description="Product search query to fetch verified offers for"),
    category: Optional[str] = Query(None, description="Category filter (e.g., laptop, phone)")
):
    """
    Fetch genuine discounts, coupon codes, and promotional deals for a given query or category.
    Returns empty list with 'No verified offers currently available' message if no active promotions match.
    """
    try:
        if query and query.strip():
            return await CouponService.get_offers_for_query(query=query.strip(), category=category)
        return await CouponService.get_featured_offers()
    except Exception as e:
        logger.exception("Failed to retrieve coupon offers for query=%r: %s", query, e)
        raise HTTPException(status_code=500, detail="Failed to fetch verified marketplace offers.")

@router.get("/featured", response_model=CouponOffersResponse)
async def get_featured_deals():
    """
    Fetch top verified marketplace discounts and promotional deals across trending categories.
    """
    try:
        return await CouponService.get_featured_offers()
    except Exception as e:
        logger.exception("Failed to retrieve featured deals: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch featured deals.")

@router.post("/extract", response_model=List[CouponOffer])
async def extract_product_offers(payload: Dict[str, Any] = Body(...)):
    """
    Extract genuine offers, discounts, and coupon details directly from a given product object.
    """
    try:
        product_data = payload.get("product") or payload
        # Normalize into model if possible
        product = NormalizedProduct.model_validate(product_data)
        offers = CouponService.extract_offers_from_product(product)
        return offers
    except Exception as e:
        logger.warning("Could not extract coupon offers from product payload: %s", e)
        return []
