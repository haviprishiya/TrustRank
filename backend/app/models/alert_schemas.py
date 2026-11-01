from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

def mask_email(email: Optional[str]) -> Optional[str]:
    """Masks an email for user privacy (e.g. j***e@example.com)."""
    if not email or "@" not in email:
        return None
    user, domain = email.strip().split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"

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
    user_email: Optional[str] = Field(None, description="Recipient email address for price drop notifications")

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
    email_notify: bool = True
    user_email_masked: Optional[str] = None
    email_status: str = Field("pending", description="pending | sent | failed | not_configured | not_requested | disabled")
    email_sent_at: Optional[str] = None
    email_error: Optional[str] = None
    last_checked_at: Optional[str] = None
    created_at: str

class UserEmailUpdate(BaseModel):
    email: str = Field(..., min_length=5, description="Valid email address for price drop alerts")

class UserEmailUpdateResponse(BaseModel):
    status: str
    email_masked: str
    message: str

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
