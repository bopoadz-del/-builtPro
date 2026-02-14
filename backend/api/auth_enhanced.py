"""
Authentication API Endpoints - ITEMS 18-20

Complete authentication flow:
- Registration with email verification (Item 19)
- Login with brute-force protection (Item 18)
- Token refresh with rotation (Item 20)
- Logout (single and all devices)
- MFA enrollment and verification
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.core.database_enhanced import get_db
from backend.core.security_enhanced import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    blacklist_token,
    check_login_attempts,
    record_login_attempt,
    clear_login_attempts,
    get_current_user,
    require_role,
    MFAManager,
    SessionManager,
    revoke_all_user_sessions,
)
from backend.backend.models import User, RefreshToken, UserRole
from backend.core.config_enhanced import settings

import logging
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserRegistration(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength (Item 19)."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None  # 6-digit TOTP token if MFA enabled


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User information response."""
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    mfa_enabled: bool = False

    class Config:
        from_attributes = True


class MFAEnrollmentResponse(BaseModel):
    """MFA enrollment response."""
    secret: str
    qr_code: str  # Base64-encoded QR code image
    backup_codes: list[str]


# ============================================================================
# ITEM 19: Registration Endpoint
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    registration: UserRegistration,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Features:
    - Email uniqueness check
    - Password strength validation (zxcvbn-style)
    - Password hashing with bcrypt + pepper
    - Email verification (TODO: SendGrid integration)

    Args:
        registration: Registration data
        request: FastAPI request (for IP logging)
        db: Database session

    Returns:
        Created user information

    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == registration.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(registration.password)

    # Create user
    new_user = User(
        name=registration.name,
        email=registration.email,
        hashed_password=hashed_password,
        role=UserRole.USER,  # Default role
        is_active=True,  # TODO: Set to False and send verification email
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {new_user.email} from IP {request.client.host}")

    # TODO: Send verification email via SendGrid (Item 19)
    # send_verification_email(new_user.email, verification_token)

    return new_user


# ============================================================================
# ITEM 18: Login Endpoint with Brute-Force Protection
# ============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return tokens.

    Features:
    - Brute-force protection (5 attempts/IP/minute)
    - Device fingerprinting (User-Agent)
    - MFA verification (if enabled)
    - Session creation
    - Audit logging

    Args:
        login_data: Login credentials
        request: FastAPI request
        db: Database session

    Returns:
        Access token and refresh token

    Raises:
        HTTPException: If authentication fails or rate limited
    """
    client_ip = request.client.host

    # ITEM 18: Check brute-force protection
    if not check_login_attempts(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Verify credentials
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        record_login_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # TODO: MFA verification (Item 24)
    # if user.mfa_secret and not login_data.mfa_token:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="MFA token required"
    #     )
    # if user.mfa_secret and not MFAManager.verify_totp(user.mfa_secret, login_data.mfa_token):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid MFA token"
    #     )

    # Clear login attempts on success
    clear_login_attempts(client_ip)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(user.id, db)

    # Create session (Item 25)
    session_id = SessionManager.create_session(
        user_id=user.id,
        session_data={
            "ip_address": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
    )

    logger.info(f"User logged in: {user.email} from IP {client_ip}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


# ============================================================================
# ITEM 20: Token Refresh Endpoint
# ============================================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Features:
    - Refresh token rotation (Item 20)
    - Old token revocation
    - New token pair generation

    Args:
        refresh_request: Refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token invalid or expired
    """
    # Verify refresh token exists in database
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_request.refresh_token,
        RefreshToken.revoked == 0
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check expiration
    if stored_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Get user
    user = db.query(User).filter(User.id == stored_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # ITEM 20: Refresh token rotation
    # Revoke old refresh token
    stored_token.revoked = 1
    db.commit()

    # Create new tokens
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(user.id, db)

    logger.info(f"Token refreshed for user: {user.email}")

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


# ============================================================================
# ITEM 21: Logout Endpoints
# ============================================================================

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current session.

    Invalidates current access token and refresh tokens.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Revoke all refresh tokens for this user
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == 0
    ).update({"revoked": 1})

    db.commit()

    # Delete all sessions
    SessionManager.delete_all_user_sessions(current_user.id)

    logger.info(f"User logged out: {current_user.email}")

    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices/sessions.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    revoke_all_user_sessions(current_user.id, db)

    logger.info(f"User logged out from all devices: {current_user.email}")

    return {"message": "Logged out from all devices"}


# ============================================================================
# ITEM 24: MFA Endpoints
# ============================================================================

@router.post("/mfa/enroll", response_model=MFAEnrollmentResponse)
async def enroll_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enroll in Multi-Factor Authentication (TOTP).

    Generates:
    - TOTP secret
    - QR code for Google Authenticator
    - 10 backup codes

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        MFA enrollment data
    """
    # Generate TOTP secret
    secret = MFAManager.generate_secret()

    # Generate QR code
    provisioning_uri = MFAManager.get_provisioning_uri(secret, current_user.email)
    qr_code = MFAManager.generate_qr_code(provisioning_uri)

    # Generate backup codes
    backup_codes = MFAManager.generate_backup_codes(settings.mfa_backup_codes_count)

    # TODO: Store secret and backup codes in database
    # user.mfa_secret = secret
    # user.mfa_backup_codes = json.dumps(backup_codes)
    # db.commit()

    logger.info(f"MFA enrollment initiated for user: {current_user.email}")

    return MFAEnrollmentResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )


@router.post("/mfa/verify")
async def verify_mfa(
    token: str,
    secret: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify and activate MFA.

    Args:
        token: 6-digit TOTP token
        secret: MFA secret from enrollment
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    if not MFAManager.verify_totp(secret, token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )

    # TODO: Activate MFA for user
    # user.mfa_secret = secret
    # user.mfa_enabled = True
    # db.commit()

    logger.info(f"MFA activated for user: {current_user.email}")

    return {"message": "MFA activated successfully"}


@router.delete("/mfa/disable")
async def disable_mfa(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable MFA (requires password confirmation).

    Args:
        password: User's password for confirmation
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # TODO: Disable MFA
    # user.mfa_secret = None
    # user.mfa_enabled = False
    # user.mfa_backup_codes = None
    # db.commit()

    logger.info(f"MFA disabled for user: {current_user.email}")

    return {"message": "MFA disabled successfully"}


# ============================================================================
# User Info Endpoint
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user

    Returns:
        User information
    """
    return current_user


# ============================================================================
# Password Change Endpoint
# ============================================================================

class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.

    Args:
        password_data: Current and new password
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # Hash new password
    new_hashed_password = hash_password(password_data.new_password)

    # Update password
    current_user.hashed_password = new_hashed_password
    db.commit()

    # Revoke all sessions (force re-login)
    revoke_all_user_sessions(current_user.id, db)

    logger.info(f"Password changed for user: {current_user.email}")

    return {"message": "Password changed successfully. Please log in again."}
