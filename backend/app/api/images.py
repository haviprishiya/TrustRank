"""Optional image endpoints.  They never disclose provider credentials."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl
import os

router = APIRouter(prefix="/images", tags=["images"])

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    size: str = "1024x1024"

class ImageAnalyzeRequest(BaseModel):
    image_url: HttpUrl

def _configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("IMAGE_PROVIDER_API_KEY", "").strip())

@router.post("/generate")
async def generate_image(request: ImageGenerateRequest):
    if not _configured():
        raise HTTPException(status_code=503, detail="Image generation provider is not configured.")
    # A provider adapter is intentionally required before making an external
    # image call; never pretend to have generated an image.
    raise HTTPException(status_code=501, detail="The configured image provider adapter is not enabled yet.")

@router.post("/analyze")
async def analyze_image(request: ImageAnalyzeRequest):
    if not _configured():
        raise HTTPException(status_code=503, detail="Image analysis provider is not configured.")
    raise HTTPException(status_code=501, detail="The configured image analysis provider adapter is not enabled yet.")
