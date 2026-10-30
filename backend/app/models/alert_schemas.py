from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PriceAlertCreate(BaseModel):
    product_id: str
    product_title: str
    marketplace: Optional[str] = "Amazon India"
    current_price: float = Field(..., gt=0, description="Current verified price in INR")
    target_price: float = Field(..., gt=0, description="User desired target price in INR")
    currency: Optional[str] = "INR"
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    email_notify: Optional[bool] = True

class PriceAlertResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    product_title: str
    marketplace: str
    initial_price: float
    current_price: float
    target_price: float
    price_difference: float
    percentage_drop_needed: float
    currency: str = "INR"
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    status: str = Field(..., description="active | target_reached | price_unavailable | disabled")
    notified: bool = False
    notification_message: Optional[str] = None
    last_checked_at: Optional[str] = None
    created_at: str

class PriceAlertStatusUpdate(BaseModel):
    status: str = Field(..., description="active | disabled")

class PriceAlertListResponse(BaseModel):
    total_alerts: int
    active_alerts: int
    target_reached_alerts: int
    alerts: List[PriceAlertResponse]
    unread_notifications: List[Dict[str, Any]] = Field(default_factory=list)

class PriceAlertCheckResult(BaseModel):
    checked_count: int
    triggered_count: int
    unavailable_count: int
    details: List[Dict[str, Any]] = Field(default_factory=list)
