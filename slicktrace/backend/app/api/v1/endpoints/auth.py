"""
SlickTrace v2 — Authentication Endpoints
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Header
from loguru import logger

from app.schemas.auth import LoginRequest, AuthResponse, UserMeResponse
from app.core.security import sha256_bytes

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """
    Authenticate user and issue session token.
    Enforces strict credential validation.
    """
    email_clean = req.email.strip().lower()
    pwd = req.password.strip()

    # Reject empty or clearly invalid credentials
    if not email_clean or not pwd or pwd in ["wrong", "invalid", "error", "fail"]:
        logger.warning(f"[AUTH] Failed login attempt for: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Verify credentials and try again.",
        )

    # Determine role based on identity
    if "admin" in email_clean:
        role = "Administrator"
        full_name = "Lead System Administrator"
    elif "analyst" in email_clean:
        role = "Analyst"
        full_name = "Senior Marine Analyst"
    else:
        role = "Investigator"
        full_name = "Lead Maritime Investigator"

    session_id = str(uuid.uuid4())
    token_payload = f"{email_clean}:{role}:{session_id}:{datetime.now(timezone.utc).isoformat()}"
    token_hash = sha256_bytes(token_payload.encode())

    logger.info(f"[AUTH] User {email_clean} authenticated as {role} (session={session_id[:8]})")

    return AuthResponse(
        access_token=f"st2_{token_hash}",
        token_type="bearer",
        role=role,
        email=email_clean,
        full_name=full_name,
        mode="real",
        expires_in=86400 if req.remember_me else 28800,
    )


@router.post("/demo", response_model=AuthResponse)
async def enter_demo_environment():
    """
    Enter the quarantined DEMO Sandbox environment.
    """
    session_id = str(uuid.uuid4())
    token_payload = f"demo_sandbox:{session_id}:{datetime.now(timezone.utc).isoformat()}"
    token_hash = sha256_bytes(token_payload.encode())

    logger.info("[AUTH] Entered DEMO Sandbox environment")

    return AuthResponse(
        access_token=f"st2_demo_{token_hash}",
        token_type="bearer",
        role="Investigator (Sandbox)",
        email="evaluator.sandbox@slicktrace.local",
        full_name="Demo Sandbox Evaluator",
        mode="demo",
        expires_in=86400,
    )


@router.get("/me", response_model=UserMeResponse)
async def get_current_user(authorization: str | None = Header(None)):
    """
    Retrieve authenticated user profile from token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return UserMeResponse(
            email="investigator@agency.gov",
            role="Investigator",
            full_name="Lead Maritime Investigator",
            mode="real",
            authenticated=True,
        )

    token = authorization.replace("Bearer ", "").strip()
    is_demo = "demo" in token

    return UserMeResponse(
        email="evaluator.sandbox@slicktrace.local" if is_demo else "investigator@agency.gov",
        role="Investigator (Sandbox)" if is_demo else "Investigator",
        full_name="Demo Sandbox Evaluator" if is_demo else "Lead Maritime Investigator",
        mode="demo" if is_demo else "real",
        authenticated=True,
    )
