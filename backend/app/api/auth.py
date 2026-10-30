import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Depends
from pydantic import BaseModel, Field, EmailStr

from app.services.auth_service import AuthService
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128, description="User password (min 6 characters)")
    name: Optional[str] = Field(default=None, max_length=100, description="Full name or display name")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: str
    last_login_at: Optional[str] = None
    welcome_email_sent: bool = False

class AuthResponse(BaseModel):
    user: UserProfile
    token: str
    message: str
    welcome_email_status: Optional[str] = None

async def _send_welcome_email_background(recipient_email: str, recipient_name: Optional[str], user_id: str):
    """Background task function to send welcome email and record status."""
    try:
        result = await EmailService.send_welcome_email(recipient_email, recipient_name)
        status = result.get("status", "unknown")
        AuthService.mark_welcome_email_sent(user_id)
        AuthService.record_email_dispatch(
            user_id=user_id,
            recipient_email=recipient_email,
            email_type="welcome_email",
            status=status,
            details=result.get("message") or result.get("error")
        )
    except Exception as e:
        logger.error("Background welcome email dispatch failed for %s: %s", recipient_email, str(e))
        AuthService.record_email_dispatch(
            user_id=user_id,
            recipient_email=recipient_email,
            email_type="welcome_email",
            status="error",
            details=str(e)
        )

@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest, background_tasks: BackgroundTasks):
    """
    Registers a new user, creates an active session token, and queues a welcome email.
    """
    try:
        user_dict = AuthService.create_user(
            email=str(request.email),
            password=request.password,
            name=request.name
        )
        token = AuthService.create_session(user_dict["id"])

        # Queue welcome email in background
        background_tasks.add_task(
            _send_welcome_email_background,
            recipient_email=user_dict["email"],
            recipient_name=user_dict["name"],
            user_id=user_dict["id"]
        )

        return AuthResponse(
            user=UserProfile(**user_dict),
            token=token,
            message="Account created successfully! A welcome email has been sent to your mail ID.",
            welcome_email_status="dispatched"
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during signup for email=%r", request.email)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, background_tasks: BackgroundTasks):
    """
    Authenticates an existing user and returns their session token.
    If welcome email was never sent, automatically queues it.
    """
    try:
        user_dict = AuthService.authenticate_user(
            email=str(request.email),
            password=request.password
        )
        token = AuthService.create_session(user_dict["id"])

        # If welcome email wasn't sent previously or user wants email on login
        if not user_dict.get("welcome_email_sent"):
            background_tasks.add_task(
                _send_welcome_email_background,
                recipient_email=user_dict["email"],
                recipient_name=user_dict["name"],
                user_id=user_dict["id"]
            )
            email_status = "dispatched"
            msg = "Signed in successfully! A welcome email has been dispatched to your mail ID."
        else:
            # Also dispatch a sign-in notification welcome email if requested
            background_tasks.add_task(
                _send_welcome_email_background,
                recipient_email=user_dict["email"],
                recipient_name=user_dict["name"],
                user_id=user_dict["id"]
            )
            email_status = "sent"
            msg = "Signed in successfully! Welcome back to TrustRank."

        return AuthResponse(
            user=UserProfile(**user_dict),
            token=token,
            message=msg,
            welcome_email_status=email_status
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during login for email=%r", request.email)
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")

@router.get("/me", response_model=UserProfile)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Retrieves the currently authenticated user based on the Bearer token.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required.")
    
    token = authorization.replace("Bearer ", "").strip()
    user_dict = AuthService.get_user_by_token(token)
    if not user_dict:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")

    return UserProfile(**user_dict)

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Invalidates the active session token.
    """
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        AuthService.delete_session(token)
    return {"message": "Signed out successfully."}
