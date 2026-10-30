import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

@pytest.fixture(autouse=True)
def setup_temp_auth_db(monkeypatch):
    """Ensure tests run against an isolated temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = tf.name
    
    monkeypatch.setattr("app.core.config.settings.AUTH_DB_PATH", temp_db_path)
    AuthService._initialized = False
    AuthService.initialize_db()
    
    yield
    
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except Exception:
        pass

def test_user_signup_and_duplicate_prevention():
    # 1. Successful user creation
    user = AuthService.create_user("shopper@example.com", "secret123", name="Jane Doe")
    assert user["email"] == "shopper@example.com"
    assert user["name"] == "Jane Doe"
    assert user["id"] is not None

    # 2. Duplicate user creation should raise ValueError
    with pytest.raises(ValueError) as exc:
        AuthService.create_user("shopper@example.com", "anotherpass")
    assert "already exists" in str(exc.value)

def test_user_login_and_password_validation():
    AuthService.create_user("user@example.com", "correctpassword", name="Alex")
    
    # 1. Login with correct password
    user = AuthService.authenticate_user("user@example.com", "correctpassword")
    assert user["email"] == "user@example.com"
    assert user["name"] == "Alex"
    
    # 2. Login with incorrect password
    with pytest.raises(ValueError) as exc:
        AuthService.authenticate_user("user@example.com", "wrongpassword")
    assert "Incorrect password" in str(exc.value)
    
    # 3. Login with non-existent email
    with pytest.raises(ValueError) as exc:
        AuthService.authenticate_user("notfound@example.com", "somepass")
    assert "No account found" in str(exc.value)

def test_session_creation_and_validation():
    user = AuthService.create_user("session_user@example.com", "securepwd")
    token = AuthService.create_session(user["id"])
    assert token is not None
    
    # Validate token
    session_user = AuthService.get_user_by_token(token)
    assert session_user is not None
    assert session_user["email"] == "session_user@example.com"
    
    # Delete token (logout)
    AuthService.delete_session(token)
    assert AuthService.get_user_by_token(token) is None

def test_welcome_email_content_generation():
    content = EmailService.generate_welcome_email_content("rahul@example.com", "Rahul Sharma")
    assert "Rahul Sharma" in content["subject"]
    assert "Rahul Sharma" in content["html"]
    assert "Intent-First Search" in content["html"]
    assert "Zero-Fabrication" in content["html"]
    assert "rahul@example.com" in content["html"]

def test_welcome_email_simulated_dispatch():
    # Without SMTP configured, send_welcome_email_sync should succeed in simulated mode
    result = EmailService.send_welcome_email_sync("tester@example.com", "Tester")
    assert result["status"] == "simulated"
    assert result["recipient"] == "tester@example.com"
    assert "Welcome email prepared" in result["message"]

def test_welcome_email_live_smtp_mock():
    with patch("smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value = instance
        with patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"):
            result = EmailService.send_welcome_email_sync("live@example.com", "Live User")
            assert result["status"] == "sent"
            assert instance.sendmail.called
