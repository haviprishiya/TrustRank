from typing import Optional, List
from pydantic import BaseModel, Field

VALID_COUPON_REPORT_REASONS = [
    "Coupon code is not working.",
    "Coupon has expired.",
    "Incorrect discount amount.",
    "Invalid coupon code.",
    "Misleading offer.",
    "Other."
]

VALID_REPORT_STATUSES = ["Pending", "Reviewed", "Resolved", "Rejected"]

class CouponReportCreate(BaseModel):
    coupon_id: str = Field(..., description="Unique identifier of the reported coupon offer")
    coupon_code: Optional[str] = Field(None, description="Coupon code string if available")
    marketplace: str = Field(..., description="Marketplace name (Amazon India, Flipkart, Myntra, etc.)")
    item_title: str = Field(..., description="Title of the promotional offer or associated product")
    reason: str = Field(..., description="One of the standard report reasons")
    description: Optional[str] = Field(None, max_length=1000, description="Optional user details explaining the issue")
    product_url: Optional[str] = Field(None, description="Direct URL to marketplace product")

class GeneralReportCreate(BaseModel):
    report_type: str = Field("product", description="Type of report: 'product' | 'coupon' | 'general'")
    target_id: str = Field(..., description="Target product or resource ID")
    item_title: Optional[str] = None
    marketplace: Optional[str] = "Amazon India"
    reason: str = Field(...)
    description: Optional[str] = Field(None, max_length=1000)

class ReportStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending | Reviewed | Resolved | Rejected")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Internal admin notes")
    disable_coupon: Optional[bool] = Field(False, description="Whether to deactivate this coupon so it no longer appears in offers")

class ReportResponse(BaseModel):
    id: str
    report_type: str
    target_id: str
    item_title: Optional[str] = None
    coupon_code: Optional[str] = None
    marketplace: str
    reason: str
    description: Optional[str] = None
    user_id: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    action_taken: Optional[str] = None
    created_at: str
    updated_at: str

class ReportListResponse(BaseModel):
    total_reports: int
    pending_count: int
    reviewed_count: int
    resolved_count: int
    rejected_count: int
    reports: List[ReportResponse]

class DisabledCouponInfo(BaseModel):
    coupon_id: str
    coupon_code: Optional[str] = None
    marketplace: Optional[str] = None
    disabled_by: Optional[str] = None
    reason: Optional[str] = None
    disabled_at: str
