from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt

router = APIRouter()
logger = logging.getLogger(__name__)

# Environment detection: default to production for security
ENV = os.getenv("ENV", "production").lower()
IS_PROD = ENV in ("prod", "production")


def _get_jwt_secret() -> str:
    """Get JWT secret, requiring it in production."""
    secret = os.getenv("JWT_SECRET_KEY")
    if secret:
        return secret

    is_prod = os.getenv("ENV", "production").lower() in ("prod", "production")
    if is_prod:
        logger.error(
            "JWT_SECRET_KEY is not set in production; "
            "auth endpoints will reject all requests"
        )
        return ""

    return "insecure-dev-secret-do-not-use-in-prod"


def _get_admin_credentials() -> tuple[str, str]:
    """Get admin credentials, requiring them in production."""
    user = os.getenv("AUTH_ADMIN_USER")
    password = os.getenv("AUTH_ADMIN_PASSWORD")

    if user and password:
        return user, password

    is_prod = os.getenv("ENV", "production").lower() in ("prod", "production")
    if is_prod:
        logger.error(
            "AUTH_ADMIN_USER and AUTH_ADMIN_PASSWORD not set in production; "
            "auth endpoints will reject login attempts"
        )
        return "", ""

    logger.warning("Using insecure dev admin credentials - do NOT use in production")
    return user or "dev-admin", password or "dev-password-insecure"


JWT_SECRET = _get_jwt_secret()
JWT_ALGORITHM = "HS256"

ADMIN_USER, ADMIN_PASSWORD = _get_admin_credentials()


@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    if not JWT_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="JWT authentication is not configured")
    if not ADMIN_USER or not ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin credentials are not configured")
    if form_data.username != ADMIN_USER or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = jwt.encode({"sub": form_data.username, "tenant_id": 1}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login")
async def legacy_login() -> dict:
    return {"status": "ok", "message": "Use /auth/token for OAuth2 login"}


@router.post("/auth/register")
async def register() -> dict:
    return {"status": "ok", "message": "User registration stub"}
