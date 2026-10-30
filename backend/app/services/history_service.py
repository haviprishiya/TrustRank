import sqlite3
import json
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.models.history_schemas import (
    HistoryItem,
    SavedProductItem,
    ProfileDashboardStats,
    CustomerProfileDetails,
    ProfileDashboardResponse
)

logger = logging.getLogger(__name__)

class HistoryService:
    _initialized = False

    @classmethod
    def get_db_connection(cls) -> sqlite3.Connection:
        db_path = settings.AUTH_DB_PATH
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        """Creates the required tables for research history and saved products."""
        if cls._initialized:
            return

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_research_history (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        category TEXT NOT NULL,
                        title TEXT NOT NULL,
                        query TEXT,
                        metadata TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_saved_products (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        marketplace TEXT,
                        price REAL,
                        original_price REAL,
                        rating REAL,
                        trust_score REAL,
                        image_url TEXT,
                        product_url TEXT,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        UNIQUE(user_id, product_id)
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_user_cat ON user_research_history(user_id, category, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_user ON user_saved_products(user_id, created_at)")
            cls._initialized = True
            logger.info("Research history and saved products tables initialized.")
        except Exception as e:
            logger.error("Failed to initialize History SQLite DB: %s", str(e))
        finally:
            conn.close()

    @classmethod
    def record_event(
        cls,
        user_id: str,
        category: str,
        title: str,
        query: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HistoryItem:
        """Records a customer research activity (search, recommendation, comparison, review, or coupon)."""
        cls.initialize_db()
        item_id = secrets.token_hex(12)
        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO user_research_history (id, user_id, category, title, query, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item_id, user_id, category, title, query, meta_json, now_iso)
                )
            return HistoryItem(
                id=item_id,
                category=category,
                title=title,
                query=query,
                metadata=metadata or {},
                created_at=now_iso
            )
        finally:
            conn.close()

    @classmethod
    def get_history(
        cls,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[HistoryItem]:
        """Retrieves history items for a specific customer, optionally filtered by category."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            if category and category.lower() != "all":
                cursor.execute(
                    """
                    SELECT id, category, title, query, metadata, created_at
                    FROM user_research_history
                    WHERE user_id = ? AND category = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, category.lower(), limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, category, title, query, metadata, created_at
                    FROM user_research_history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit)
                )
            rows = cursor.fetchall()
            items = []
            for r in rows:
                try:
                    meta = json.loads(r["metadata"]) if r["metadata"] else {}
                except Exception:
                    meta = {}
                items.append(
                    HistoryItem(
                        id=r["id"],
                        category=r["category"],
                        title=r["title"],
                        query=r["query"],
                        metadata=meta,
                        created_at=r["created_at"]
                    )
                )
            return items
        finally:
            conn.close()

    @classmethod
    def clear_history(cls, user_id: str, category: Optional[str] = None) -> int:
        """Clears all history or history for a specific category for the user."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                if category and category.lower() != "all":
                    cursor = conn.execute(
                        "DELETE FROM user_research_history WHERE user_id = ? AND category = ?",
                        (user_id, category.lower())
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM user_research_history WHERE user_id = ?",
                        (user_id,)
                    )
                return cursor.rowcount
        finally:
            conn.close()

    @classmethod
    def save_product(cls, user_id: str, product_data: Dict[str, Any]) -> SavedProductItem:
        """Saves a product to customer's personal bookmarks/saved products list."""
        cls.initialize_db()
        saved_id = secrets.token_hex(12)
        product_id = str(product_data.get("product_id") or product_data.get("id"))
        title = product_data.get("title") or "Unnamed Product"
        marketplace = product_data.get("marketplace") or "Amazon India"
        price = product_data.get("price") or product_data.get("current_price")
        original_price = product_data.get("original_price")
        rating = product_data.get("rating")
        trust_score = product_data.get("trust_score") or product_data.get("trustrank_score")
        image_url = product_data.get("image_url") or (product_data.get("image_candidates")[0] if product_data.get("image_candidates") else None)
        product_url = product_data.get("product_url")
        metadata = product_data.get("metadata") or {}
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO user_saved_products (
                        id, user_id, product_id, title, marketplace, price, original_price,
                        rating, trust_score, image_url, product_url, metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, product_id) DO UPDATE SET
                        title = excluded.title,
                        price = excluded.price,
                        original_price = excluded.original_price,
                        rating = excluded.rating,
                        trust_score = excluded.trust_score,
                        image_url = excluded.image_url,
                        product_url = excluded.product_url,
                        metadata = excluded.metadata
                    """,
                    (
                        saved_id, user_id, product_id, title, marketplace,
                        float(price) if price is not None else None,
                        float(original_price) if original_price is not None else None,
                        float(rating) if rating is not None else None,
                        float(trust_score) if trust_score is not None else None,
                        image_url, product_url, json.dumps(metadata), now_iso
                    )
                )
            return SavedProductItem(
                id=saved_id,
                product_id=product_id,
                title=title,
                marketplace=marketplace,
                price=float(price) if price is not None else None,
                original_price=float(original_price) if original_price is not None else None,
                rating=float(rating) if rating is not None else None,
                trust_score=float(trust_score) if trust_score is not None else None,
                image_url=image_url,
                product_url=product_url,
                metadata=metadata,
                created_at=now_iso
            )
        finally:
            conn.close()

    @classmethod
    def remove_saved_product(cls, user_id: str, product_id: str) -> bool:
        """Removes a product from customer's saved products list."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM user_saved_products WHERE user_id = ? AND product_id = ?",
                    (user_id, product_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @classmethod
    def get_saved_products(cls, user_id: str) -> List[SavedProductItem]:
        """Retrieves all products saved by the customer."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, product_id, title, marketplace, price, original_price,
                       rating, trust_score, image_url, product_url, metadata, created_at
                FROM user_saved_products
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
            items = []
            for r in rows:
                try:
                    meta = json.loads(r["metadata"]) if r["metadata"] else {}
                except Exception:
                    meta = {}
                items.append(
                    SavedProductItem(
                        id=r["id"],
                        product_id=r["product_id"],
                        title=r["title"],
                        marketplace=r["marketplace"],
                        price=r["price"],
                        original_price=r["original_price"],
                        rating=r["rating"],
                        trust_score=r["trust_score"],
                        image_url=r["image_url"],
                        product_url=r["product_url"],
                        metadata=meta,
                        created_at=r["created_at"]
                    )
                )
            return items
        finally:
            conn.close()

    @classmethod
    def get_dashboard_summary(cls, user_id: str, user_dict: Optional[Dict[str, Any]] = None) -> ProfileDashboardResponse:
        """Aggregates all profile stats, saved products, and recent research history."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()

            # 1. Total counts by category
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM user_research_history
                WHERE user_id = ?
                GROUP BY category
                """,
                (user_id,)
            )
            counts_map = {row["category"]: row["count"] for row in cursor.fetchall()}

            # 2. Saved products count
            cursor.execute("SELECT COUNT(*) as count FROM user_saved_products WHERE user_id = ?", (user_id,))
            saved_count = cursor.fetchone()["count"]

            stats = ProfileDashboardStats(
                total_searches=counts_map.get("search", 0),
                total_recommendations=counts_map.get("recommendation", 0),
                total_comparisons=counts_map.get("comparison", 0),
                total_reviews_analyzed=counts_map.get("review_analysis", 0),
                total_coupons_viewed=counts_map.get("coupon", 0),
                total_saved_products=saved_count
            )

            # 3. Recent history items
            recent_items = cls.get_history(user_id=user_id, limit=20)

            # 4. Saved products list
            saved_products = cls.get_saved_products(user_id=user_id)

            # 5. Extract recently viewed products from history metadata
            recently_viewed: List[Dict[str, Any]] = []
            seen_pids = set()
            for it in recent_items:
                if it.category in ("recommendation", "review_analysis", "saved"):
                    p_info = it.metadata.get("product") or it.metadata
                    pid = p_info.get("id") or p_info.get("product_id") or it.title
                    if pid and pid not in seen_pids:
                        seen_pids.add(pid)
                        recently_viewed.append({
                            "title": it.title,
                            "marketplace": p_info.get("marketplace") or "Amazon India",
                            "price": p_info.get("price") or p_info.get("current_price"),
                            "rating": p_info.get("rating"),
                            "trust_score": p_info.get("trust_score"),
                            "image_url": p_info.get("image_url"),
                            "category": it.category,
                            "viewed_at": it.created_at
                        })

            customer_details = None
            if user_dict:
                customer_details = CustomerProfileDetails(
                    id=user_dict["id"],
                    email=user_dict["email"],
                    name=user_dict.get("name"),
                    created_at=user_dict.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    last_login_at=user_dict.get("last_login_at"),
                    welcome_email_sent=bool(user_dict.get("welcome_email_sent", False)),
                    is_active=bool(user_dict.get("is_active", True))
                )

            return ProfileDashboardResponse(
                customer=customer_details,
                stats=stats,
                recent_history=recent_items,
                saved_products=saved_products,
                recently_viewed_products=recently_viewed[:10]
            )
        finally:
            conn.close()
