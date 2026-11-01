import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Depends

from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.models.report_schemas import (
    CouponReportCreate,
    GeneralReportCreate,
    ReportStatusUpdate,
    ReportResponse,
    ReportListResponse,
    DisabledCouponInfo
)

router = APIRouter(prefix="/reports", tags=["Reports & Moderation"])
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

@router.post("/coupons", response_model=ReportResponse)
async def submit_coupon_report(
    payload: CouponReportCreate,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Submits a user report for a coupon offer (e.g. not working, expired, incorrect discount).
    Prevents duplicate submissions from the same user for an active report.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        report = ReportService.submit_coupon_report(user_id=user_key, data=payload)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to submit coupon report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to submit coupon report. Please try again.")

@router.post("", response_model=ReportResponse)
async def submit_general_report(
    payload: GeneralReportCreate,
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
):
    """
    Submits a general or product report, maintaining a unified reporting architecture.
    """
    try:
        _, user_key = get_current_user_or_guest(authorization, x_guest_id)
        report = ReportService.submit_general_report(user_id=user_key, data=payload)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to submit report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to submit report.")

@router.get("", response_model=ReportListResponse)
async def get_reports(
    report_type: Optional[str] = Query(None, description="'coupon' | 'product' | 'all'"),
    status: Optional[str] = Query(None, description="'Pending' | 'Reviewed' | 'Resolved' | 'Rejected' | 'all'"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Admin endpoint to retrieve reported items filtered by type and status.
    """
    try:
        return ReportService.get_reports(report_type=report_type, status=status, limit=limit)
    except Exception as e:
        logger.exception("Failed to load reports: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load reports.")

@router.put("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: str,
    payload: ReportStatusUpdate,
    authorization: Optional[str] = Header(None)
):
    """
    Admin endpoint to mark a report as Pending, Reviewed, Resolved, or Rejected.
    Allows admin to investigate and disable expired or invalid coupons.
    """
    try:
        user_dict, user_key = get_current_user_or_guest(authorization, None)
        admin_name = user_dict.get("name") if user_dict else user_key
        return ReportService.update_report_status(
            report_id=report_id,
            data=payload,
            admin_user=admin_name or "admin"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to update report status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update report status.")

@router.get("/disabled-coupons", response_model=List[DisabledCouponInfo])
async def get_disabled_coupons():
    """
    Retrieves all coupons that have been deactivated by admin moderation.
    """
    try:
        return ReportService.get_disabled_coupons()
    except Exception as e:
        logger.exception("Failed to load disabled coupons: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load disabled coupons.")
