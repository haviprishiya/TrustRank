import os
from app.api.products import router as products_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import settings
from app.api.endpoints import router as api_router
from app.api.images import router as images_router
from app.api.auth import router as auth_router
from app.api.coupons import router as coupons_router
from app.api.history import router as history_router
from app.api.alerts import router as alerts_router
from app.api.reports import router as reports_router
import asyncio
from app.services.alert_service import AlertService
from app.services.report_service import ReportService

app = FastAPI(
     
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="TrustRank: Production-Quality Real-Time Shopping Research & Recommendation Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.include_router(products_router)
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Endpoints
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(images_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(coupons_router, prefix=settings.API_V1_PREFIX)
app.include_router(history_router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)

# Periodic Price Drop Monitor
async def _periodic_price_check_worker():
    while True:
        try:
            await asyncio.sleep(900)  # Check every 15 minutes
            await AlertService.check_alerts()
        except asyncio.CancelledError:
            break
        except Exception:
            pass

@app.on_event("startup")
async def start_periodic_price_monitor():
    AlertService.initialize_db()
    ReportService.initialize_db()
    asyncio.create_task(_periodic_price_check_worker())

# Static Files & SPA Routing
# Check for static directories (trustrank/static or frontend/dist)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        content={
            "message": "TrustRank API is running. Static frontend index.html not yet built in /static.",
            "api_docs": "/docs",
            "health": "/api/health"
        }
    )

@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    # Check if a static file directly exists in STATIC_DIR
    potential_file = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(potential_file):
        return FileResponse(potential_file)

    # If not an API route, serve the SPA index.html for client-side routing
    if not full_path.startswith("api/") and not full_path.startswith("docs") and not full_path.startswith("openapi.json") and not full_path.startswith("redoc"):
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
