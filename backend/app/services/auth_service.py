import sqlite3
import hashlib
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    _initialized = False

    @classmethod
    def get_db_connection(cls) -> sqlite3.Connection:
        db_path = settings.AUTH_DB_PATH
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        """Creates the required tables in SQLite if they don't exist."""
        if cls._initialized:
            return
        
        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_login_at TEXT,
                        welcome_email_sent INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_dispatches (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        recipient_email TEXT NOT NULL,
                        email_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
            cls._initialized = True
            logger.info("Auth SQLite database initialized at %s", settings.AUTH_DB_PATH)
        except Exception as e:
            logger.error("Failed to initialize Auth SQLite DB: %s", str(e))
        finally:
            conn.close()

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a secure salt."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Constant-time verification of password against stored PBKDF2 hash."""
        computed_hash, _ = AuthService.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def validate_email_format(email: str) -> bool:
        email = email.strip()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    @classmethod
    def create_user(cls, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Registers a new user account."""
        cls.initialize_db()
        email_clean = email.strip().lower()

        if not cls.validate_email_format(email_clean):
            raise ValueError("Invalid email format.")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        user_id = secrets.token_hex(12)
        pwd_hash, salt = cls.hash_password(password)
        now_iso = datetime.now(timezone.utc).isoformat()
        name_clean = name.strip() if name and name.strip() else None

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO users (id, email, name, password_hash, salt, created_at, last_login_at, welcome_email_sent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (user_id, email_clean, name_clean, pwd_hash, salt, now_iso, now_iso)
                )
            return {
                "id": user_id,
                "email": email_clean,
                "name": name_clean,
                "created_at": now_iso,
                "last_login_at": now_iso,
                "welcome_email_sent": False
            }
        except sqlite3.IntegrityError:
            raise ValueError("An account with this email address already exists. Please sign in instead.")
        finally:
            conn.close()

    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Dict[str, Any]:
        """Authenticates user credentials."""
        cls.initialize_db()
        email_clean = email.strip().lower()

        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name, password_hash, salt, created_at, last_login_at, welcome_email_sent, is_active FROM users WHERE email = ?",
                (email_clean,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("No account found with this email address. Please sign up.")

            if not row["is_active"]:
                raise ValueError("This account has been deactivated.")

            if not cls.verify_password(password, row["password_hash"], row["salt"]):
                raise ValueError("Incorrect password. Please verify and try again.")

            now_iso = datetime.now(timezone.utc).isoformat()
            with conn:
                conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_iso, row["id"]))

            return {
                "id": row["id"],
                "email": row["email"],
                "name": row["name"],
                "created_at": row["created_at"],
                "last_login_at": now_iso,
                "welcome_email_sent": bool(row["welcome_email_sent"])
            }
        finally:
            conn.close()

    @classmethod
    def mark_welcome_email_sent(cls, user_id: str):
        """Marks that welcome email was sent to user."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("UPDATE users SET welcome_email_sent = 1 WHERE id = ?", (user_id,))
        finally:
            conn.close()

    @classmethod
    def create_session(cls, user_id: str) -> str:
        """Creates a session token for an authenticated user."""
        cls.initialize_db()
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.AUTH_TOKEN_EXPIRE_DAYS)

        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                    (token, user_id, now.isoformat(), expires_at.isoformat())
                )
            return token
        finally:
            conn.close()

    @classmethod
    def get_user_by_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Retrieves user profile associated with a valid session token."""
        if not token:
            return None
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.email, u.name, u.created_at, u.last_login_at, u.welcome_email_sent, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND u.is_active = 1
                """,
                (token,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                # Expired session
                with conn:
                    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                return None

            return {
                "id": row["id"],
                "email": row["email"],
                "name": row["name"],
                "created_at": row["created_at"],
                "last_login_at": row["last_login_at"],
                "welcome_email_sent": bool(row["welcome_email_sent"])
            }
        finally:
            conn.close()

    @classmethod
    def delete_session(cls, token: str):
        """Invalidates a session token (sign out)."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        finally:
            conn.close()

    @classmethod
    def record_email_dispatch(cls, user_id: Optional[str], recipient_email: str, email_type: str, status: str, details: Optional[str] = None):
        """Logs an email dispatch record."""
        cls.initialize_db()
        conn = cls.get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO email_dispatches (id, user_id, recipient_email, email_type, status, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        secrets.token_hex(12),
                        user_id,
                        recipient_email,
                        email_type,
                        status,
                        details,
                        datetime.now(timezone.utc).isoformat()
                    )
                )
        except Exception as e:
            logger.error("Failed to record email dispatch: %s", str(e))
        finally:
            conn.close()
