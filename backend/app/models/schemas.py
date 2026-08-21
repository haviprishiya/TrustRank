from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class QuestionOption(BaseModel):
    value: str
    label: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    description: Optional[str] = None

class RequirementQuestion(BaseModel):
    id: str
    question: str
    subtext: Optional[str] = None
    type: str = "single_choice"  # single_choice, multi_choice, range_slider, chip_select, text
    options: List[QuestionOption] = []
    default_value: Any = None
    category: str = "general"
    importance_weight: float = 1.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    unit: Optional[str] = None

class SearchIntent(BaseModel):
    raw_query: str
    detected_category: str
    category_display_name: str
    confidence: float = 0.9
    extracted_budget: Optional[float] = None
    extracted_brands: List[str] = []
    extracted_features: List[str] = []
    target_audience_or_use: Optional[str] = None
    normalized_query: str
    keywords: List[str] = []

class UserRequirementAnswers(BaseModel):
    query: str
    category: Optional[str] = None
    answers: Dict[str, Any] = {}

class MarketplaceOffer(BaseModel):
    marketplace: str  # "Amazon India", "Flipkart", "Official Store"
    provider: str
    product_url: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: str = "INR"
    in_stock: bool = True
    rating: Optional[float] = None
    review_count: Optional[int] = None
    seller_name: Optional[str] = None
    delivery_info: Optional[str] = None

class ReviewAnalysisResult(BaseModel):
    has_detailed_reviews: bool = False
    source_note: str
    total_reviews_analyzed: int = 0
    positive_percentage: float = 0.0
    neutral_percentage: float = 0.0
    negative_percentage: float = 0.0
    most_praised_features: List[str] = []
    common_complaints: List[str] = []
    recurring_themes: List[str] = []
    rating_distribution: Dict[str, float] = {}
    summary: str = ""

class NormalizedProduct(BaseModel):
    id: str
    title: str
    brand: str
    category: str
    image_url: Optional[str] = ""
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: str = "INR"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: str = "In Stock"
    product_url: str
    marketplace: str
    provider: str
    seller: Optional[str] = None
    source: Optional[str] = None
    specifications: Dict[str, str] = {}
    features: List[str] = []
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    offers: List[MarketplaceOffer] = []
    review_analysis: Optional[ReviewAnalysisResult] = None
    raw_data: Optional[Dict[str, Any]] = None

class ScoredRecommendation(BaseModel):
    product: NormalizedProduct
    trustrank_score: float = 0.0  # 0 - 100
    requirement_match_percentage: float = 0.0  # 0 - 100
    budget_fit_score: float = 0.0  # 0 - 100
    value_for_money: str = "Good"  # Excellent, Great, Good, Fair
    value_for_money_score: float = 0.0
    
    # Transparent multi-factor scoring breakdown
    requirement_match_score: float = 0.0
    price_value_score: float = 0.0
    rating_score: float = 0.0
    review_confidence_score: float = 0.0
    availability_score: float = 0.0
    source_reliability_score: float = 0.0
    scoring_breakdown_explanation: Dict[str, str] = {}
    
    positive_reasons: List[str] = []
    negative_reasons: List[str] = []
    neutral_observations: List[str] = []
    best_for_you_explanation: str = ""
    category_badges: List[str] = []

class BrandAnalytics(BaseModel):
    brand: str
    product_count: int
    average_rating: Optional[float] = None
    total_reviews: int
    average_price: Optional[float] = None
    positive_percentage: float
    negative_percentage: float

class MarketplaceAnalytics(BaseModel):
    marketplace: str
    product_count: int
    average_price: float
    average_rating: float
    total_reviews: int

class PriceBracketAnalytics(BaseModel):
    bracket_label: str
    count: int
    min_price: float
    max_price: float

class RatingBracketAnalytics(BaseModel):
    rating_range: str
    count: int
    percentage: float

class AnalyticsDashboardData(BaseModel):
    total_products_analyzed: int
    total_reviews_represented: int
    average_rating: float
    positive_review_percentage: float
    neutral_review_percentage: float
    negative_review_percentage: float
    brand_analysis: List[BrandAnalytics] = []
    marketplace_analysis: List[MarketplaceAnalytics] = []
    price_distribution: List[PriceBracketAnalytics] = []
    rating_distribution: List[RatingBracketAnalytics] = []
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProviderStatusInfo(BaseModel):
    provider_id: str
    name: str
    marketplace: str
    status: str  # "active", "credentials_required", "rate_limited", "unavailable", "fallback_active"
    message: str
    configured: bool
    env_keys_required: List[str] = []
    latency_ms: Optional[float] = None
    items_fetched: int = 0

class RecommendationPipelineResponse(BaseModel):
    query: str
    intent: SearchIntent
    total_products_found: int
    deduplicated_products_count: int
    recommendations: List[ScoredRecommendation]
    top_5_comparison: List[ScoredRecommendation]
    best_for_you: Optional[ScoredRecommendation] = None
    best_value: Optional[ScoredRecommendation] = None
    best_reviewed: Optional[ScoredRecommendation] = None
    best_alternative: Optional[ScoredRecommendation] = None
    analytics: AnalyticsDashboardData
    provider_statuses: List[ProviderStatusInfo]
    execution_time_seconds: float
