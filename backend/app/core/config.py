import os
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # The documented .env file lives at the repository root, even when Uvicorn
    # is launched from backend/.
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )
    
    APP_NAME: str = "TrustRank"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000"
    ]
    
    # Live Marketplace Providers Credentials (configured securely via environment)
    # 1. Amazon Official PA-API 5.0 (India: webservices.amazon.in)
    AMAZON_PAAPI_ACCESS_KEY: str = os.getenv("AMAZON_PAAPI_ACCESS_KEY", "")
    AMAZON_PAAPI_SECRET_KEY: str = os.getenv("AMAZON_PAAPI_SECRET_KEY", "")
    AMAZON_PAAPI_TAG: str = os.getenv("AMAZON_PAAPI_TAG", "")
    AMAZON_PAAPI_REGION: str = os.getenv("AMAZON_PAAPI_REGION", "in")
    
    # 2. Flipkart Affiliate API
    FLIPKART_AFFILIATE_ID: str = os.getenv("FLIPKART_AFFILIATE_ID", "")
    FLIPKART_AFFILIATE_TOKEN: str = os.getenv("FLIPKART_AFFILIATE_TOKEN", "")
    
    # 3. RapidAPI Real-Time Product Data (Amazon & Flipkart)
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
    RAPIDAPI_AMAZON_HOST: str = os.getenv("RAPIDAPI_AMAZON_HOST", "real-time-amazon-data.p.rapidapi.com")
    RAPIDAPI_FLIPKART_HOST: str = os.getenv("RAPIDAPI_FLIPKART_HOST", "real-time-flipkart-data.p.rapidapi.com")
    
    # 4. SerpApi (Google Shopping India / Amazon Data API in INR)
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    
    # 5. Open Product Data Providers (Open Beauty Facts / Open Food Facts)
    ENABLE_OPEN_DATA_PROVIDER: bool = True
    
    # 6. Live Search Provider
    ENABLE_LIVE_SEARCH_PROVIDER: bool = True

    # 7. Additional Store Providers
    ENABLE_MYNTRA_PROVIDER: bool = True
    ENABLE_CROMA_PROVIDER: bool = True

    # 8. Amazon Creators API settings
    AMAZON_CREATORS_CREDENTIAL_ID: str = os.getenv("AMAZON_CREATORS_CREDENTIAL_ID", "")
    AMAZON_CREATORS_CREDENTIAL_SECRET: str = os.getenv("AMAZON_CREATORS_CREDENTIAL_SECRET", "")
    AMAZON_CREATORS_CREDENTIAL_VERSION: str = os.getenv("AMAZON_CREATORS_CREDENTIAL_VERSION", "")
    AMAZON_CREATORS_PARTNER_TAG: str = os.getenv("AMAZON_CREATORS_PARTNER_TAG", "")
    AMAZON_CREATORS_TOKEN_ENDPOINT: str = os.getenv("AMAZON_CREATORS_TOKEN_ENDPOINT", "https://api.amazon.com/auth/o2/token")

    # 9. Authentication & User Database Settings
    AUTH_DB_PATH: str = os.getenv("AUTH_DB_PATH", str(Path(__file__).resolve().parents[2] / "trustrank_users.db"))
    AUTH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("AUTH_TOKEN_EXPIRE_DAYS", "30"))
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "trustrank-auth-secure-secret-key-2026")

    # 10. SMTP Email Settings (for welcome email & notifications)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in {"true", "1", "yes"}
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() in {"true", "1", "yes"}
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "welcome@trustrank.ai")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "TrustRank Shopping Intelligence")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value):
        """Treat common deployment labels such as 'release' as debug disabled."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "false", "0", "no", "off", ""}:
                return False
            if normalized in {"development", "dev", "debug", "true", "1", "yes", "on"}:
                return True
        return value

settings = Settings()
