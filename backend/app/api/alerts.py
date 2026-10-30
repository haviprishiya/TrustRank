import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends

from app.services.auth_service import AuthService
from app.services.alert_service import AlertService
from app.models.alert_schemas import (
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertStatusUpdate,
    PriceAlertListResponse,
    PriceAlertCheckResult
)

router = APIRouter(prefix="/alerts", tags=["Price Drop Alerts"])
logger = logging.getLogger(__name__)

def get_current_user_or_guest(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        user_dict = AuthService.get_user_by_token(token)
        if user_dict:
            return user_dict, f"user_{user_dict['id']}"

    if x_guest_id and x_guest_id.strip():
        guest_clean = x_guest_id.strip()[:64]
        return None, f"guest_{guest_clean}"

    return None, "guest_anonymous"

@router.get("", response_model=PriceAlertListResponse)
async def get_alerts(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Retrieves all price drop alerts and target-reached notifications for the current user.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        return AlertService.get_user_alerts(user_id=user_key)
    except Exception as e:
        logger.exception("Failed to retrieve price alerts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load price drop alerts.")

@router.post("", response_model=PriceAlertResponse)
async def create_alert(
    req: PriceAlertCreate,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Creates a new price drop alert or updates existing target price for the product.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        return AlertService.create_alert(user_id=user_key, data=req)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to create price alert: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create price drop alert.")

@router.put("/{alert_id}/status", response_model=dict)
async def update_alert_status(
    alert_id: str,
    req: PriceAlertStatusUpdate,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Enables or disables an alert ('active' or 'disabled').
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        success = AlertService.update_alert_status(user_id=user_key, alert_id=alert_id, new_status=req.status)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found.")
        return {"status": "success", "new_status": req.status, "message": f"Alert is now {req.status}."}
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to update alert status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update alert status.")

@router.delete("/{alert_id}", response_model=dict)
async def delete_alert(
    alert_id: str,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Deletes a price drop alert.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        success = AlertService.delete_alert(user_id=user_key, alert_id=alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found.")
        return {"status": "success", "message": "Price alert deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete alert: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete alert.")

@router.post("/check", response_model=PriceAlertCheckResult)
async def trigger_price_check(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Triggers an immediate verified price check against active alerts using existing marketplace providers.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        result = await AlertService.check_alerts(user_id=user_key)
        return result
    except Exception as e:
        logger.exception("Failed to run price check: %s", e)
        raise HTTPException(status_code=500, detail="Failed to complete price check.")
