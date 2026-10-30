from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class HistoryItem(BaseModel):
    id: str
    category: str = Field(..., description="search | recommendation | comparison | review_analysis | coupon")
    title: str
    query: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

class HistoryRecordRequest(BaseModel):
    category: str = Field(..., description="search | recommendation | comparison | review_analysis | coupon")
    title: str
    query: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SavedProductItem(BaseModel):
    id: str
    product_id: str
    title: str
    marketplace: Optional[str] = "Amazon India"
    price: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = None
    trust_score: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

class SaveProductRequest(BaseModel):
    product_id: str
    title: str
    marketplace: Optional[str] = "Amazon India"
    price: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = None
    trust_score: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProfileDashboardStats(BaseModel):
    total_searches: int = 0
    total_recommendations: int = 0
    total_comparisons: int = 0
    total_reviews_analyzed: int = 0
    total_coupons_viewed: int = 0
    total_saved_products: int = 0

class CustomerProfileDetails(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: str
    last_login_at: Optional[str] = None
    welcome_email_sent: bool = False
    is_active: bool = True

class ProfileDashboardResponse(BaseModel):
    customer: Optional[CustomerProfileDetails] = None
    stats: ProfileDashboardStats
    recent_history: List[HistoryItem] = Field(default_factory=list)
    saved_products: List[SavedProductItem] = Field(default_factory=list)
    recently_viewed_products: List[Dict[str, Any]] = Field(default_factory=list)

class HistoryListResponse(BaseModel):
    category: Optional[str] = None
    total: int
    items: List[HistoryItem]
