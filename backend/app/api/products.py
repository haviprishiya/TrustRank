import logging
import re
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.brightdata_service import BrightDataServiceError, scrape_amazon, search_amazon

router = APIRouter()
logger = logging.getLogger(__name__)

class ProductRequest(BaseModel):
    query: str | None = Field(default=None, min_length=2, max_length=200, description="Natural-language Amazon product search query")
    # Retained only for API-client compatibility. The browser always sends a
    # normal search query and never asks shoppers for this field.
    url: str | None = Field(default=None, min_length=10, max_length=2048, description="Legacy Amazon product URL")

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must not be blank.")
        return query

    @field_validator("url")
    @classmethod
    def validate_amazon_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        url = value.strip()
        if re.fullmatch(r"[A-Z0-9]{10}", url, re.IGNORECASE):
            return f"https://www.amazon.in/dp/{url.upper()}"
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"https", "http"} or not re.fullmatch(r"(?:[a-z0-9-]+\.)*amazon\.[a-z.]+", host):
            raise ValueError("url must point to an Amazon domain.")
        if not re.search(r"/(?:dp|gp/product)/[A-Z0-9]{10}(?:[/?]|$)", parsed.path, re.IGNORECASE):
            raise ValueError("url must be an Amazon product URL containing a valid ASIN.")
        return url

    @model_validator(mode="after")
    def require_query_or_legacy_url(self):
        if not self.query and not self.url:
            raise ValueError("query is required.")
        return self

@router.post("/products/scrape")
async def scrape_product(request: ProductRequest):
    try:
        products = await run_in_threadpool(search_amazon, request.query) if request.query else await run_in_threadpool(scrape_amazon, request.url)
        return {"products": products, "count": len(products)}
    except BrightDataServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected Amazon product request failure for query=%r", request.query)
        raise HTTPException(status_code=500, detail="Amazon search failed. Please try again.")
