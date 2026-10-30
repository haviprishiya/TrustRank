from typing import List, Optional
from pydantic import BaseModel, Field

class CouponOffer(BaseModel):
    id: str
    title: str
    applicable_product: str
    marketplace: str  # Amazon India, Flipkart, Myntra, etc.
    current_price: float
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    coupon_code: Optional[str] = None
    has_coupon_code: bool = False
    offer_type: str = "Marketplace Discount"  # "Coupon Code", "Bank Offer", "Direct Discount", "Festive Deal"
    description: str
    terms: Optional[str] = None
    expiry_date: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    verified: bool = True

class CouponOffersResponse(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    total_offers: int = 0
    offers: List[CouponOffer] = Field(default_factory=list)
    message: Optional[str] = None
