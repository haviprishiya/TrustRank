import sqlite3
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set

from app.core.config import settings
from app.models.report_schemas import (
    CouponReportCreate,
    GeneralReportCreate,
    ReportStatusUpdate,
    ReportResponse,
    ReportListResponse,
    DisabledCouponInfo,
    VALID_COUPON_REPORT_REASONS,
    VALID_REPORT_STATUSES
)

logger = logging.getLogger(__name__)

class ReportService:
    _initialized = False

    @classmethod
    def get_db_connection(cls) -> sqlite3.Connection:
        conn = sqlite3.connect(settings.AUTH_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        """Initializes the unified reports and disabled_coupons tables."""
        if cls._initialized:
            return

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,          -- 'coupon' | 'product' | 'general'
                        target_id TEXT NOT NULL,            -- coupon_id or product_id
                        item_title TEXT,
                        coupon_code TEXT,
                        marketplace TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        description TEXT,
                        user_id TEXT,
                        product_url TEXT,
                        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Reviewed' | 'Resolved' | 'Rejected'
                        admin_notes TEXT,
                        action_taken TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS disabled_coupons (
                        coupon_id TEXT PRIMARY KEY,
                        coupon_code TEXT,
                        marketplace TEXT,
                        disabled_by TEXT,
                        reason TEXT,
                        disabled_at TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_type_status ON reports(report_type, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_target_user ON reports(target_id, user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_disabled_coupons_code ON disabled_coupons(coupon_code)")
            cls._initialized = True
            logger.info("Unified Reports SQLite tables initialized at %s", settings.AUTH_DB_PATH)
        except Exception as e:
            logger.error("Failed to initialize reports table: %s", str(e))
        finally:
            conn.close()

    @classmethod
    def submit_coupon_report(cls, user_id: str, data: CouponReportCreate) -> ReportResponse:
        """
        Submits a report for an invalid, expired, or non-working coupon.
        Enforces validation of reason and prevents duplicate submissions for active reports.
        """
        cls.initialize_db()

        # 1. Validate Reason
        clean_reason = data.reason.strip()
        if clean_reason not in VALID_COUPON_REPORT_REASONS:
            raise ValueError(f"Invalid report reason. Must be one of: {', '.join(VALID_COUPON_REPORT_REASONS)}")

        if not data.coupon_id or not data.coupon_id.strip():
            raise ValueError("Coupon ID cannot be empty.")

        now_iso = datetime.now(timezone.utc).isoformat()
        report_id = f"rep_{secrets.token_hex(10)}"

        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # 2. Duplicate Prevention: Check if same user/guest already reported this coupon
                cursor.execute(
                    """
                    SELECT id, status FROM reports
                    WHERE report_type = 'coupon' AND target_id = ? AND user_id = ? AND status IN ('Pending', 'Reviewed')
                    """,
                    (data.coupon_id.strip(), user_id)
                )
                existing = cursor.fetchone()
                if existing:
                    raise ValueError(
                        "You have already submitted an active report for this coupon. Our moderation team is investigating."
                    )

                clean_desc = data.description.strip() if data.description and data.description.strip() else None
                clean_code = data.coupon_code.strip() if data.coupon_code and data.coupon_code.strip() else None

                cursor.execute(
                    """
                    INSERT INTO reports (
                        id, report_type, target_id, item_title, coupon_code, marketplace,
                        reason, description, user_id, product_url, status, created_at, updated_at
                    ) VALUES (?, 'coupon', ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
                    """,
                    (
                        report_id, data.coupon_id.strip(), data.item_title.strip(),
                        clean_code, data.marketplace.strip(), clean_reason,
                        clean_desc, user_id, data.product_url, now_iso, now_iso
                    )
                )

            return ReportResponse(
                id=report_id,
                report_type="coupon",
                target_id=data.coupon_id.strip(),
                item_title=data.item_title.strip(),
                coupon_code=clean_code,
                marketplace=data.marketplace.strip(),
                reason=clean_reason,
                description=clean_desc,
                user_id=user_id,
                status="Pending",
                admin_notes=None,
                action_taken=None,
                created_at=now_iso,
                updated_at=now_iso
            )
        finally:
            conn.close()

    @classmethod
    def submit_general_report(cls, user_id: str, data: GeneralReportCreate) -> ReportResponse:
        """Submits general or product reports to keep the reporting system unified."""
        cls.initialize_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        report_id = f"rep_{secrets.token_hex(10)}"

        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO reports (
                        id, report_type, target_id, item_title, coupon_code, marketplace,
                        reason, description, user_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, 'Pending', ?, ?)
                    """,
                    (
                        report_id, data.report_type, data.target_id.strip(),
                        data.item_title, data.marketplace or "Amazon India",
                        data.reason.strip(), data.description, user_id, now_iso, now_iso
                    )
                )
            return ReportResponse(
                id=report_id,
                report_type=data.report_type,
                target_id=data.target_id.strip(),
                item_title=data.item_title,
                coupon_code=None,
                marketplace=data.marketplace or "Amazon India",
                reason=data.reason.strip(),
                description=data.description,
                user_id=user_id,
                status="Pending",
                admin_notes=None,
                action_taken=None,
                created_at=now_iso,
                updated_at=now_iso
            )
        finally:
            conn.close()

    @classmethod
    def get_reports(
        cls,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> ReportListResponse:
        """Retrieves reports with filtering and summary status counters."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()

            # Query items
            query = "SELECT * FROM reports WHERE 1=1"
            params: List[Any] = []
            if report_type and report_type != "all":
                query += " AND report_type = ?"
                params.append(report_type)
            if status and status != "all":
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            reports = [
                ReportResponse(
                    id=r["id"],
                    report_type=r["report_type"],
                    target_id=r["target_id"],
                    item_title=r["item_title"],
                    coupon_code=r["coupon_code"],
                    marketplace=r["marketplace"],
                    reason=r["reason"],
                    description=r["description"],
                    user_id=r["user_id"],
                    status=r["status"],
                    admin_notes=r["admin_notes"],
                    action_taken=r["action_taken"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                )
                for r in rows
            ]

            # Summary counters
            cursor.execute("SELECT status, COUNT(*) as cnt FROM reports GROUP BY status")
            counts = {r["status"]: r["cnt"] for r in cursor.fetchall()}

            return ReportListResponse(
                total_reports=sum(counts.values()),
                pending_count=counts.get("Pending", 0),
                reviewed_count=counts.get("Reviewed", 0),
                resolved_count=counts.get("Resolved", 0),
                rejected_count=counts.get("Rejected", 0),
                reports=reports
            )
        finally:
            conn.close()

    @classmethod
    def update_report_status(
        cls,
        report_id: str,
        data: ReportStatusUpdate,
        admin_user: str = "admin"
    ) -> ReportResponse:
        """
        Updates the status of a report (Pending, Reviewed, Resolved, Rejected).
        Optionally deactivates/disables the invalid coupon so it no longer appears in feeds.
        """
        if data.status not in VALID_REPORT_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_REPORT_STATUSES)}")

        cls.initialize_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
                rep = cursor.fetchone()
                if not rep:
                    raise KeyError(f"Report with id '{report_id}' not found.")

                action_taken = rep["action_taken"]

                # If admin chooses to disable the coupon
                if data.disable_coupon:
                    action_taken = "coupon_disabled"
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO disabled_coupons (
                            coupon_id, coupon_code, marketplace, disabled_by, reason, disabled_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rep["target_id"],
                            rep["coupon_code"],
                            rep["marketplace"],
                            admin_user,
                            data.admin_notes or rep["reason"],
                            now_iso
                        )
                    )
                    logger.info("Coupon %s (%s) disabled by admin %s", rep["target_id"], rep["coupon_code"], admin_user)

                clean_notes = data.admin_notes.strip() if data.admin_notes and data.admin_notes.strip() else rep["admin_notes"]

                cursor.execute(
                    """
                    UPDATE reports
                    SET status = ?, admin_notes = ?, action_taken = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (data.status, clean_notes, action_taken, now_iso, report_id)
                )

                cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
                updated = cursor.fetchone()

                return ReportResponse(
                    id=updated["id"],
                    report_type=updated["report_type"],
                    target_id=updated["target_id"],
                    item_title=updated["item_title"],
                    coupon_code=updated["coupon_code"],
                    marketplace=updated["marketplace"],
                    reason=updated["reason"],
                    description=updated["description"],
                    user_id=updated["user_id"],
                    status=updated["status"],
                    admin_notes=updated["admin_notes"],
                    action_taken=updated["action_taken"],
                    created_at=updated["created_at"],
                    updated_at=updated["updated_at"]
                )
        finally:
            conn.close()

    @classmethod
    def get_disabled_coupon_ids(cls) -> Set[str]:
        """Returns set of all disabled coupon IDs and upper-case coupon codes."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT coupon_id, coupon_code FROM disabled_coupons")
            rows = cursor.fetchall()
            disabled: Set[str] = set()
            for r in rows:
                if r["coupon_id"]:
                    disabled.add(r["coupon_id"])
                if r["coupon_code"]:
                    disabled.add(r["coupon_code"].strip().upper())
            return disabled
        finally:
            conn.close()

    @classmethod
    def get_disabled_coupons(cls) -> List[DisabledCouponInfo]:
        """Returns list of all disabled coupon details."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM disabled_coupons ORDER BY disabled_at DESC")
            return [
                DisabledCouponInfo(
                    coupon_id=r["coupon_id"],
                    coupon_code=r["coupon_code"],
                    marketplace=r["marketplace"],
                    disabled_by=r["disabled_by"],
                    reason=r["reason"],
                    disabled_at=r["disabled_at"]
                )
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()
