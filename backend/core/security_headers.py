"""
Security Headers Middleware - ITEMS 41-42

Implements comprehensive security headers for production deployment:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing prevention)
- X-XSS-Protection (XSS filter)
- Referrer-Policy (Referrer information control)
- Content-Security-Policy (CSP) with nonce generation
- Permissions-Policy (Feature permissions)

All headers configured according to OWASP security best practices.
"""

import secrets
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.config_enhanced import settings
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ITEM 41: Security Headers
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # HSTS: Force HTTPS for 1 year (31536000 seconds)
        # includeSubDomains: Apply to all subdomains
        # preload: Eligible for browser preload lists
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={settings.hsts_max_age}; includeSubDomains; preload"
            )

        # X-Frame-Options: Prevent clickjacking
        # DENY: Don't allow framing at all
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        # nosniff: Don't allow browser to override Content-Type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable XSS filter (legacy browsers)
        # 1; mode=block: Enable and block page if XSS detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        # strict-origin-when-cross-origin: Send origin only for cross-origin HTTPS
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Control browser features
        # Disable unnecessary features for security
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # X-Permitted-Cross-Domain-Policies: Adobe Flash/PDF
        # none: Don't allow cross-domain access
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # X-Download-Options: IE8+ download handling
        # noopen: Don't open downloads directly
        response.headers["X-Download-Options"] = "noopen"

        return response


# ============================================================================
# ITEM 42: Content Security Policy (CSP)
# ============================================================================

class CSPMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy middleware with nonce generation.

    CSP prevents XSS attacks by controlling which resources can be loaded.
    Uses nonce-based approach for inline scripts/styles.
    """

    def __init__(self, app, csp_policy: str = None):
        """
        Initialize CSP middleware.

        Args:
            app: FastAPI application
            csp_policy: Custom CSP policy (optional)
        """
        super().__init__(app)
        self.csp_policy = csp_policy or settings.csp_policy

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add CSP header with nonce to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with CSP header
        """
        # Generate nonce for this request
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        # Process request
        response = await call_next(request)

        # Build CSP policy with nonce
        csp_directives = self._build_csp_directives(nonce)

        # Add CSP header
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Also add Report-Only header for testing (optional)
        if settings.environment.value == "staging":
            response.headers["Content-Security-Policy-Report-Only"] = "; ".join(
                csp_directives
            )

        return response

    def _build_csp_directives(self, nonce: str) -> list[str]:
        """
        Build CSP directives with nonce.

        Args:
            nonce: Generated nonce for this request

        Returns:
            List of CSP directives
        """
        directives = [
            # Default: Only same origin
            "default-src 'self'",

            # Scripts: Self + nonce + specific domains
            # Note: 'unsafe-inline' and 'unsafe-eval' needed for React in dev
            # In production, remove these and use nonce
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",

            # Styles: Self + nonce + inline (for Tailwind)
            f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline' https://fonts.googleapis.com",

            # Images: Self + data URIs + external CDNs
            "img-src 'self' data: https: blob:",

            # Fonts: Self + Google Fonts
            "font-src 'self' data: https://fonts.gstatic.com",

            # Connect: API endpoints
            "connect-src 'self' https://api.cerebrum.ai wss://api.cerebrum.ai",

            # Media: Self only
            "media-src 'self'",

            # Objects: None (no Flash, Java applets)
            "object-src 'none'",

            # Frame: None (don't allow framing)
            "frame-src 'none'",

            # Frame ancestors: None (can't be framed)
            "frame-ancestors 'none'",

            # Base URI: Self only
            "base-uri 'self'",

            # Form action: Self only
            "form-action 'self'",

            # Upgrade insecure requests (HTTP -> HTTPS)
            "upgrade-insecure-requests",

            # Block mixed content
            "block-all-mixed-content",
        ]

        # Add report URI in production
        if settings.is_production:
            directives.append("report-uri https://cerebrum.report-uri.com/r/d/csp/enforce")

        return directives


# ============================================================================
# ITEM 37: CORS Configuration
# ============================================================================

def get_cors_config() -> dict:
    """
    Get CORS configuration based on environment.

    Returns:
        CORS configuration dict for FastAPI CORSMiddleware
    """
    # Production: Strict origins only
    if settings.is_production:
        return {
            "allow_origins": settings.cors_allow_origins,
            "allow_credentials": settings.cors_allow_credentials,
            "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Accept",
                "Accept-Language",
                "Content-Type",
                "Authorization",
                "X-Correlation-ID",
                "X-Request-ID",
            ],
            "expose_headers": [
                "X-Correlation-ID",
                "X-Request-ID",
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ],
            "max_age": 3600,  # Cache preflight for 1 hour
        }

    # Development: More permissive
    else:
        return {
            "allow_origins": settings.cors_allow_origins or ["http://localhost:3000"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "expose_headers": ["*"],
            "max_age": 600,
        }


# ============================================================================
# CSP Nonce Helper
# ============================================================================

def get_csp_nonce(request: Request) -> str:
    """
    Get CSP nonce for current request.

    Usage in templates:
        <script nonce="{{ get_csp_nonce(request) }}">...</script>

    Args:
        request: FastAPI request

    Returns:
        CSP nonce string
    """
    return getattr(request.state, "csp_nonce", "")


# ============================================================================
# Security Headers Configuration
# ============================================================================

SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), payment=(), "
        "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
    ),
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Download-Options": "noopen",
}


def add_security_headers(response: Response) -> Response:
    """
    Add all security headers to response.

    Utility function for manual header addition.

    Args:
        response: FastAPI response

    Returns:
        Response with security headers added
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SecurityHeadersMiddleware",
    "CSPMiddleware",
    "get_cors_config",
    "get_csp_nonce",
    "add_security_headers",
    "SECURITY_HEADERS",
]
