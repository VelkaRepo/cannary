"""
CanaryFile Engine - Listener Server Core
FastAPI application for receiving, logging, and dispatching alerts for canary token triggers.
"""

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Response, status, APIRouter
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import base64

from server.config import settings
from server.database import DatabaseHandler
from server.notifier import WebhookNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("canaryfile.server")

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Active Defense Canary Token listener server for detecting unauthorized document access."
)

# CORS middleware enabling cross-origin requests for web bug triggers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database & Notifier instances
db = DatabaseHandler(db_path=settings.db_path)
notifier = WebhookNotifier(
    webhook_url=settings.webhook_url,
    platform=settings.webhook_platform
)

# 1x1 Transparent GIF pixel (35 bytes base64 encoded)
GIF_1X1_BYTES = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


# Pydantic Schemas for API
class TokenCreateRequest(BaseModel):
    token_id: str = Field(..., description="Unique token identifier")
    label: Optional[str] = Field(default="", description="Descriptive memo or label for tracking context")
    file_type: Optional[str] = Field(default="pdf", description="Document type (pdf, docx, etc.)")


class TokenResponse(BaseModel):
    token_id: str
    label: str
    file_type: str
    created_at: str
    is_active: bool


def get_client_ip(request: Request) -> str:
    """Extract real client IP address considering proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "127.0.0.1"


# Define API Router for trigger listener & management endpoints
router = APIRouter()


@router.get("/health", tags=["System"])
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/t/{token_id}", tags=["Trigger Listener"])
@router.post("/t/{token_id}", tags=["Trigger Listener"])
async def canary_trigger_endpoint(
    token_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Primary Canary Token trigger endpoint.
    Extracts IP address, User-Agent, and HTTP headers, logs the hit to SQLite,
    dispatches an async alert notification, and returns a 1x1 transparent GIF.
    """
    src_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown User-Agent")
    headers_dict = dict(request.headers)
    method = request.method
    query_params = str(request.query_params)

    # Log trigger event to database
    hit_data = db.log_hit(
        token_id=token_id,
        src_ip=src_ip,
        user_agent=user_agent,
        headers=headers_dict,
        method=method,
        query_params=query_params
    )
    
    logger.warning(f"🚨 CANARY TRIGGERED! Token ID: {token_id} | IP: {src_ip} | UA: {user_agent}")

    # Fetch token metadata if available
    token_meta = db.get_token(token_id)

    # Queue async alert notification
    if settings.webhook_url or notifier.webhook_url:
        background_tasks.add_task(notifier.send_alert, hit_data, token_meta)

    # Respond with 1x1 GIF image or 204 No Content
    if settings.return_gif:
        return Response(content=GIF_1X1_BYTES, media_type="image/gif")
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api/v1/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, tags=["Token Management"])
async def register_canary_token(payload: TokenCreateRequest):
    """Register a new canary token."""
    result = db.register_token(
        token_id=payload.token_id,
        label=payload.label or "",
        file_type=payload.file_type or "pdf"
    )
    return result


@router.get("/api/v1/tokens", response_model=List[Dict[str, Any]], tags=["Token Management"])
async def list_canary_tokens():
    """List all registered canary tokens."""
    return db.list_tokens()


@router.get("/api/v1/hits", response_model=List[Dict[str, Any]], tags=["Telemetry Logs"])
async def list_trigger_hits(token_id: Optional[str] = None):
    """Retrieve recorded trigger hits telemetry."""
    return db.list_hits(token_id=token_id)


# Include router for both root and /trigger-test path prefixes
app.include_router(router)
app.include_router(router, prefix="/trigger-test")

