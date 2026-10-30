import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Depends

from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.models.history_schemas import (
    HistoryItem,
    HistoryRecordRequest,
    SavedProductItem,
    SaveProductRequest,
    ProfileDashboardResponse,
    HistoryListResponse
)

router = APIRouter(prefix="/history", tags=["Research History & Profile"])
logger = logging.getLogger(__name__)

def get_current_user_or_guest(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Extracts the authenticated user from the session token.
    Falls back to a guest identifier if unauthenticated, allowing guests to track history locally.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        user_dict = AuthService.get_user_by_token(token)
        if user_dict:
            return user_dict, f"user_{user_dict['id']}"

    if x_guest_id and x_guest_id.strip():
        guest_clean = x_guest_id.strip()[:64]
        return None, f"guest_{guest_clean}"

    # Default fallback guest
    return None, "guest_anonymous"

@router.get("/dashboard", response_model=ProfileDashboardResponse)
async def get_profile_dashboard(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Retrieves the customer profile overview, metrics counters (searches, recommendations,
    comparisons, reviews, offers), saved products, and recent research history.
    """
    try:
        user_dict, user_key = get_current_user_or_guest(authorization, x_guest_id)
        return HistoryService.get_dashboard_summary(user_id=user_key, user_dict=user_dict)
    except Exception as e:
        logger.exception("Failed to retrieve profile dashboard: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load customer profile dashboard.")

@router.get("", response_model=HistoryListResponse)
async def get_research_history(
    category: Optional[str] = Query(None, description="search | recommendation | comparison | review_analysis | coupon | all"),
    limit: int = Query(50, ge=1, le=200),
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Retrieves the customer's research history filtered by category.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        items = HistoryService.get_history(user_id=user_key, category=category, limit=limit)
        return HistoryListResponse(
            category=category or "all",
            total=len(items),
            items=items
        )
    except Exception as e:
        logger.exception("Failed to retrieve research history: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load research history.")

@router.post("/record", response_model=HistoryItem)
async def record_research_activity(
    req: HistoryRecordRequest,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Records a research action (search, recommendation view, comparison view, review analysis, or coupon view).
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        item = HistoryService.record_event(
            user_id=user_key,
            category=req.category,
            title=req.title,
            query=req.query,
            metadata=req.metadata
        )
        return item
    except Exception as e:
        logger.exception("Failed to record research activity: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record research history.")

@router.delete("/clear")
async def clear_research_history(
    category: Optional[str] = Query(None, description="Clear specific category or all if omitted"),
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Clears the customer's research history (either a specific category or everything).
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        deleted_count = HistoryService.clear_history(user_id=user_key, category=category)
        return {
            "status": "success",
            "message": f"Cleared {deleted_count} research history records.",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.exception("Failed to clear research history: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clear research history.")

@router.get("/saved", response_model=List[SavedProductItem])
async def get_saved_products(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Returns list of products bookmarked/saved by the customer.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        return HistoryService.get_saved_products(user_id=user_key)
    except Exception as e:
        logger.exception("Failed to get saved products: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve saved products.")

@router.post("/save", response_model=SavedProductItem)
async def save_product(
    req: SaveProductRequest,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Saves a product to the customer's personal bookmarks list.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        return HistoryService.save_product(user_id=user_key, product_data=req.model_dump())
    except Exception as e:
        logger.exception("Failed to save product: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save product.")

@router.delete("/save/{product_id}")
async def remove_saved_product(
    product_id: str,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Removes a product from the customer's saved list.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        success = HistoryService.remove_saved_product(user_id=user_key, product_id=product_id)
        return {
            "status": "success" if success else "not_found",
            "message": "Product removed from saved items." if success else "Product was not found in saved items."
        }
    except Exception as e:
        logger.exception("Failed to remove saved product: %s", e)
        raise HTTPException(status_code=500, detail="Failed to remove saved product.")
