import sqlite3
import secrets
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from app.core.config import settings
from app.models.alert_schemas import (
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertListResponse,
    PriceAlertCheckResult
)
from app.providers.registry import provider_registry
from app.services.email_service import EmailService
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

class AlertService:
    _initialized = False

    @classmethod
    def get_db_connection(cls) -> sqlite3.Connection:
        db_path = settings.AUTH_DB_PATH
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        """Initializes the price_alerts table in SQLite."""
        if cls._initialized:
            return

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        product_title TEXT NOT NULL,
                        marketplace TEXT NOT NULL,
                        initial_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        target_price REAL NOT NULL,
                        currency TEXT DEFAULT 'INR',
                        image_url TEXT,
                        product_url TEXT,
                        email_notify INTEGER DEFAULT 1,
                        status TEXT NOT NULL, -- 'active' | 'target_reached' | 'price_unavailable' | 'disabled'
                        notified INTEGER DEFAULT 0,
                        notification_message TEXT,
                        last_checked_at TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user_status ON price_alerts(user_id, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON price_alerts(status)")
            cls._initialized = True
            logger.info("Price alerts SQLite table initialized at %s", settings.AUTH_DB_PATH)
        except Exception as e:
            logger.error("Failed to initialize price_alerts table: %s", str(e))
        finally:
            conn.close()

    @classmethod
    def create_alert(cls, user_id: str, data: PriceAlertCreate) -> PriceAlertResponse:
        """
        Creates a new price drop alert or updates an existing alert's target price
        for the same product to prevent duplicates.
        """
        cls.initialize_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if data.target_price <= 0:
            raise ValueError("Target price must be greater than zero.")
            
        conn = cls.get_db_connection()
        try:
            with conn:
                # Check for existing alert for this user and product
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, status FROM price_alerts WHERE user_id = ? AND product_id = ?",
                    (user_id, data.product_id)
                )
                existing = cursor.fetchone()

                if existing:
                    alert_id = existing["id"]
                    # If target price is met right away by current price
                    new_status = "target_reached" if data.current_price <= data.target_price else "active"
                    notified = 1 if new_status == "target_reached" else 0
                    msg = f"Price target reached! Current price ₹{data.current_price:,.0f} meets your target of ₹{data.target_price:,.0f}." if new_status == "target_reached" else None

                    conn.execute(
                        """
                        UPDATE price_alerts
                        SET target_price = ?, current_price = ?, status = ?, notified = ?,
                            notification_message = ?, email_notify = ?, product_url = ?, image_url = ?
                        WHERE id = ?
                        """,
                        (
                            data.target_price, data.current_price, new_status, notified,
                            msg, 1 if data.email_notify else 0, data.product_url, data.image_url, alert_id
                        )
                    )
                else:
                    alert_id = secrets.token_hex(12)
                    new_status = "target_reached" if data.current_price <= data.target_price else "active"
                    notified = 1 if new_status == "target_reached" else 0
                    msg = f"Price target reached! Current price ₹{data.current_price:,.0f} meets your target of ₹{data.target_price:,.0f}." if new_status == "target_reached" else None

                    conn.execute(
                        """
                        INSERT INTO price_alerts (
                            id, user_id, product_id, product_title, marketplace,
                            initial_price, current_price, target_price, currency,
                            image_url, product_url, email_notify, status, notified,
                            notification_message, last_checked_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            alert_id, user_id, data.product_id, data.product_title,
                            data.marketplace or "Amazon India", data.current_price,
                            data.current_price, data.target_price, data.currency or "INR",
                            data.image_url, data.product_url, 1 if data.email_notify else 0,
                            new_status, notified, msg, now_iso, now_iso
                        )
                    )

            diff = round(data.current_price - data.target_price, 2)
            drop_needed = round((diff / data.current_price * 100), 1) if data.current_price > 0 and diff > 0 else 0.0

            return PriceAlertResponse(
                id=alert_id,
                user_id=user_id,
                product_id=data.product_id,
                product_title=data.product_title,
                marketplace=data.marketplace or "Amazon India",
                initial_price=data.current_price,
                current_price=data.current_price,
                target_price=data.target_price,
                price_difference=diff,
                percentage_drop_needed=drop_needed,
                currency=data.currency or "INR",
                image_url=data.image_url,
                product_url=data.product_url,
                status=new_status,
                notified=bool(notified),
                notification_message=msg,
                last_checked_at=now_iso,
                created_at=now_iso
            )
        finally:
            conn.close()

    @classmethod
    def get_user_alerts(cls, user_id: str) -> PriceAlertListResponse:
        """Retrieves all price alerts and in-app notifications for a user."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, product_id, product_title, marketplace,
                       initial_price, current_price, target_price, currency,
                       image_url, product_url, email_notify, status, notified,
                       notification_message, last_checked_at, created_at
                FROM price_alerts
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()

            alerts: List[PriceAlertResponse] = []
            unread_notifications: List[Dict[str, Any]] = []
            active_count = 0
            reached_count = 0

            for r in rows:
                diff = round(r["current_price"] - r["target_price"], 2)
                drop_needed = round((diff / r["current_price"] * 100), 1) if r["current_price"] > 0 and diff > 0 else 0.0
                status = r["status"]
                if status == "active":
                    active_count += 1
                elif status == "target_reached":
                    reached_count += 1

                item = PriceAlertResponse(
                    id=r["id"],
                    user_id=r["user_id"],
                    product_id=r["product_id"],
                    product_title=r["product_title"],
                    marketplace=r["marketplace"],
                    initial_price=r["initial_price"],
                    current_price=r["current_price"],
                    target_price=r["target_price"],
                    price_difference=diff,
                    percentage_drop_needed=drop_needed,
                    currency=r["currency"] or "INR",
                    image_url=r["image_url"],
                    product_url=r["product_url"],
                    status=status,
                    notified=bool(r["notified"]),
                    notification_message=r["notification_message"],
                    last_checked_at=r["last_checked_at"],
                    created_at=r["created_at"]
                )
                alerts.append(item)

                if status == "target_reached":
                    unread_notifications.append({
                        "id": f"notif_{r['id']}",
                        "alert_id": r["id"],
                        "product_title": r["product_title"],
                        "current_price": r["current_price"],
                        "target_price": r["target_price"],
                        "marketplace": r["marketplace"],
                        "message": r["notification_message"] or f"Price dropped to ₹{r['current_price']:,.0f}! Target of ₹{r['target_price']:,.0f} reached.",
                        "product_url": r["product_url"],
                        "created_at": r["last_checked_at"] or r["created_at"]
                    })

            return PriceAlertListResponse(
                total_alerts=len(alerts),
                active_alerts=active_count,
                target_reached_alerts=reached_count,
                alerts=alerts,
                unread_notifications=unread_notifications
            )
        finally:
            conn.close()

    @classmethod
    def update_alert_status(cls, user_id: str, alert_id: str, new_status: str) -> bool:
        """Enables or disables an alert."""
        if new_status not in {"active", "disabled"}:
            raise ValueError("Status must be either 'active' or 'disabled'.")
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE price_alerts SET status = ? WHERE id = ? AND user_id = ?",
                    (new_status, alert_id, user_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @classmethod
    def delete_alert(cls, user_id: str, alert_id: str) -> bool:
        """Deletes a price drop alert."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM price_alerts WHERE id = ? AND user_id = ?",
                    (alert_id, user_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @classmethod
    async def check_alerts(cls, user_id: Optional[str] = None) -> PriceAlertCheckResult:
        """
        Periodically checks product prices using existing, supported marketplace data providers.
        Triggers alert only when a verified price is at or below the target price.
        Never invents missing prices or claims drops without verified data.
        """
        cls.initialize_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    """
                    SELECT id, user_id, product_id, product_title, marketplace,
                           initial_price, current_price, target_price, email_notify,
                           status, notified, product_url
                    FROM price_alerts
                    WHERE user_id = ? AND status IN ('active', 'price_unavailable')
                    """,
                    (user_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, user_id, product_id, product_title, marketplace,
                           initial_price, current_price, target_price, email_notify,
                           status, notified, product_url
                    FROM price_alerts
                    WHERE status IN ('active', 'price_unavailable')
                    """
                )
            alerts = cursor.fetchall()
        finally:
            conn.close()

        checked_count = len(alerts)
        triggered_count = 0
        unavailable_count = 0
        details = []

        for alt in alerts:
            alert_id = alt["id"]
            p_title = alt["product_title"]
            mkt = alt["marketplace"]
            target = alt["target_price"]
            already_notified = bool(alt["notified"])

            # Query existing providers for live prices
            try:
                # Search across existing configured marketplace providers
                live_products = await provider_registry.search_all(query=p_title[:50], category="general", limit=5)
            except Exception as e:
                logger.warning("Marketplace search failed while checking price alert %s: %s", alert_id, e)
                live_products = []

            # Find matching product from live providers
            matched_product = None
            for p in live_products:
                if p.current_price and p.current_price > 0:
                    # Match by ASIN / product_id or title overlap
                    if p.id == alt["product_id"] or (p.asin and alt["product_id"] and p.asin in alt["product_id"]):
                        matched_product = p
                        break
                    # High title similarity fallback
                    words_a = set(p_title.lower().split()[:5])
                    words_b = set(p.title.lower().split()[:5])
                    if len(words_a & words_b) >= 3:
                        matched_product = p
                        break

            conn = cls.get_db_connection()
            try:
                with conn:
                    if matched_product and matched_product.current_price and matched_product.current_price > 0:
                        verified_price = float(matched_product.current_price)
                        if verified_price <= target:
                            # Target reached!
                            new_status = "target_reached"
                            triggered_count += 1
                            msg = f"Target price reached! Verified price on {mkt} is ₹{verified_price:,.0f} (Target was ₹{target:,.0f})."

                            # Only send notification once
                            if not already_notified:
                                conn.execute(
                                    """
                                    UPDATE price_alerts
                                    SET current_price = ?, status = ?, notified = 1,
                                        notification_message = ?, last_checked_at = ?
                                    WHERE id = ?
                                    """,
                                    (verified_price, new_status, msg, now_iso, alert_id)
                                )
                                # Dispatch email if user is registered with valid email
                                if alt["email_notify"] and alt["user_id"].startswith("user_"):
                                    real_uid = alt["user_id"].replace("user_", "")
                                    user_cursor = conn.cursor()
                                    user_cursor.execute("SELECT email, name FROM users WHERE id = ?", (real_uid,))
                                    u_row = user_cursor.fetchone()
                                    if u_row and u_row["email"]:
                                        asyncio.create_task(
                                            EmailService.send_price_drop_email(
                                                recipient_email=u_row["email"],
                                                recipient_name=u_row["name"],
                                                product_title=p_title,
                                                target_price=target,
                                                current_price=verified_price,
                                                marketplace=mkt,
                                                product_url=alt["product_url"] or matched_product.product_url
                                            )
                                        )
                            else:
                                conn.execute(
                                    "UPDATE price_alerts SET current_price = ?, last_checked_at = ? WHERE id = ?",
                                    (verified_price, now_iso, alert_id)
                                )

                            details.append({
                                "alert_id": alert_id,
                                "product_title": p_title,
                                "verified_price": verified_price,
                                "target_price": target,
                                "status": "target_reached",
                                "message": msg
                            })
                        else:
                            # Active, price checked
                            conn.execute(
                                """
                                UPDATE price_alerts
                                SET current_price = ?, status = 'active', last_checked_at = ?
                                WHERE id = ?
                                """,
                                (verified_price, now_iso, alert_id)
                            )
                            details.append({
                                "alert_id": alert_id,
                                "product_title": p_title,
                                "verified_price": verified_price,
                                "target_price": target,
                                "status": "active",
                                "message": f"Checked: ₹{verified_price:,.0f} (Target ₹{target:,.0f})"
                            })
                    else:
                        # Price unavailable from live feeds - do NOT fabricate!
                        unavailable_count += 1
                        conn.execute(
                            """
                            UPDATE price_alerts
                            SET status = 'price_unavailable', last_checked_at = ?
                            WHERE id = ?
                            """,
                            (now_iso, alert_id)
                        )
                        details.append({
                            "alert_id": alert_id,
                            "product_title": p_title,
                            "status": "price_unavailable",
                            "message": "Live price currently unavailable from authorized marketplace feed."
                        })
            finally:
                conn.close()

        return PriceAlertCheckResult(
            checked_count=checked_count,
            triggered_count=triggered_count,
            unavailable_count=unavailable_count,
            details=details
        )
