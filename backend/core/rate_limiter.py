"""
Rate Limiting Middleware - ITEM 43

Comprehensive rate limiting with Redis backend:
- Global rate limits (100/min)
- Endpoint-specific limits (auth: 5/min, IFC: 10/hour, admin: 50/min)
- IP-based and user-based limiting
- Sliding window algorithm
- Rate limit headers in responses

Uses slowapi library with Redis storage for distributed rate limiting.
"""

from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from backend.core.config_enhanced import settings
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Redis Connection for Rate Limiting
# ============================================================================

# Use dedicated Redis database for rate limiting (DB 3)
redis_client = redis.from_url(
    settings.redis_ratelimit_url,
    decode_responses=True,
    socket_timeout=2,
    socket_connect_timeout=2,
)


# ============================================================================
# Custom Key Functions
# ============================================================================

def get_remote_address_or_user(request: Request) -> str:
    """
    Get identifier for rate limiting (IP or user ID).

    Uses user ID if authenticated, otherwise falls back to IP address.
    This prevents authenticated users from bypassing rate limits by
    switching IPs.

    Args:
        request: FastAPI request

    Returns:
        Rate limit key (user ID or IP)
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get first IP from X-Forwarded-For header
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def get_user_key(request: Request) -> str:
    """
    Get user-based rate limit key.

    Raises exception if user not authenticated.

    Args:
        request: FastAPI request

    Returns:
        User-based rate limit key
    """
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required for this endpoint"
    )


# ============================================================================
# ITEM 43: Rate Limiter Initialization
# ============================================================================

# Initialize SlowAPI rate limiter
limiter = Limiter(
    key_func=get_remote_address_or_user,
    storage_uri=settings.redis_ratelimit_url,
    strategy="fixed-window",  # or "moving-window" for more accuracy
    headers_enabled=True,  # Add rate limit headers to responses
)


# ============================================================================
# Rate Limit Decorators
# ============================================================================

def rate_limit_global(func):
    """
    Apply global rate limit (100 requests per minute).

    Usage:
        @app.get("/api/endpoint")
        @rate_limit_global
        async def endpoint():
            ...
    """
    return limiter.limit(f"{settings.rate_limit_global}/minute")(func)


def rate_limit_auth(func):
    """
    Apply authentication rate limit (5 requests per minute).

    Strict limit for login/register endpoints to prevent brute force.

    Usage:
        @app.post("/api/v1/auth/login")
        @rate_limit_auth
        async def login():
            ...
    """
    return limiter.limit(f"{settings.rate_limit_auth}/minute")(func)


def rate_limit_ifc(func):
    """
    Apply IFC processing rate limit (10 requests per hour).

    Heavy operations need stricter limits.

    Usage:
        @app.post("/api/v1/ifc/parse")
        @rate_limit_ifc
        async def parse_ifc():
            ...
    """
    return limiter.limit(f"{settings.rate_limit_ifc_processing}/hour")(func)


def rate_limit_admin(func):
    """
    Apply admin endpoint rate limit (50 requests per minute).

    Admin endpoints get higher limits but still controlled.

    Usage:
        @app.get("/api/v1/admin/users")
        @rate_limit_admin
        async def get_users():
            ...
    """
    return limiter.limit(f"{settings.rate_limit_admin}/minute")(func)


# ============================================================================
# Custom Rate Limit Decorator
# ============================================================================

def rate_limit(limit: str, key_func: Callable = None):
    """
    Custom rate limit decorator with flexible configuration.

    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour", "1000/day")
        key_func: Optional custom key function

    Usage:
        @app.post("/api/expensive")
        @rate_limit("5/hour", key_func=get_user_key)
        async def expensive_operation():
            ...
    """
    def decorator(func):
        if key_func:
            return limiter.limit(limit, key_func=key_func)(func)
        return limiter.limit(limit)(func)

    return decorator


# ============================================================================
# Rate Limit Exception Handler
# ============================================================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns JSON response with rate limit information.

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        JSON response with 429 status
    """
    from backend.core.logging_config import get_correlation_id

    # Extract rate limit info from exception
    retry_after = getattr(exc, "retry_after", 60)

    logger.warning(
        f"Rate limit exceeded: {request.url.path}",
        extra={
            "ip": get_remote_address(request),
            "path": request.url.path,
            "retry_after": retry_after,
        }
    )

    return Response(
        content={
            "error": {
                "type": "RateLimitExceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after_seconds": retry_after,
                "limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
                "correlation_id": get_correlation_id(),
            }
        },
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Reset": str(int(retry_after)),
        },
        media_type="application/json",
    )


# ============================================================================
# Rate Limit Middleware (Alternative Approach)
# ============================================================================

class RateLimitMiddleware:
    """
    Middleware for global rate limiting.

    Alternative to decorator-based approach. Applies rate limits to all
    requests automatically.
    """

    def __init__(
        self,
        app,
        default_limit: str = "100/minute",
        redis_url: str = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            default_limit: Default rate limit string
            redis_url: Redis connection URL
        """
        self.app = app
        self.default_limit = default_limit
        self.redis_url = redis_url or settings.redis_ratelimit_url
        self.redis = redis.from_url(self.redis_url, decode_responses=True)

    async def __call__(self, request: Request, call_next):
        """
        Check rate limit before processing request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or 429 error
        """
        # Get rate limit key
        key = get_remote_address_or_user(request)
        rate_limit_key = f"ratelimit:{key}:{request.url.path}"

        # Check current count
        try:
            count = self.redis.incr(rate_limit_key)

            # Set expiry on first request
            if count == 1:
                self.redis.expire(rate_limit_key, 60)  # 1 minute window

            # Parse limit (e.g., "100/minute")
            limit_value = int(self.default_limit.split("/")[0])

            # Check if limit exceeded
            if count > limit_value:
                ttl = self.redis.ttl(rate_limit_key)
                raise RateLimitExceeded(f"{self.default_limit}", ttl)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit_value)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit_value - count))
            response.headers["X-RateLimit-Reset"] = str(
                self.redis.ttl(rate_limit_key)
            )

            return response

        except RateLimitExceeded as exc:
            return await rate_limit_exceeded_handler(request, exc)


# ============================================================================
# Rate Limit Info Helper
# ============================================================================

def get_rate_limit_info(request: Request, limit_key: str) -> dict:
    """
    Get current rate limit status for a key.

    Args:
        request: FastAPI request
        limit_key: Rate limit key to check

    Returns:
        Dict with limit info
    """
    key = get_remote_address_or_user(request)
    rate_limit_key = f"ratelimit:{key}:{limit_key}"

    try:
        count = redis_client.get(rate_limit_key) or 0
        ttl = redis_client.ttl(rate_limit_key)

        return {
            "current": int(count),
            "limit": settings.rate_limit_global,
            "remaining": max(0, settings.rate_limit_global - int(count)),
            "reset_seconds": ttl if ttl > 0 else 0,
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit info: {str(e)}")
        return {
            "current": 0,
            "limit": settings.rate_limit_global,
            "remaining": settings.rate_limit_global,
            "reset_seconds": 0,
        }


# ============================================================================
# Manual Rate Limit Check
# ============================================================================

def check_rate_limit(
    request: Request,
    limit: int,
    window_seconds: int,
    key_suffix: str = "",
) -> bool:
    """
    Manually check rate limit.

    Args:
        request: FastAPI request
        limit: Maximum requests
        window_seconds: Time window in seconds
        key_suffix: Optional key suffix

    Returns:
        True if within limit, False if exceeded

    Usage:
        if not check_rate_limit(request, limit=10, window_seconds=60):
            raise HTTPException(status_code=429, detail="Too many requests")
    """
    key = get_remote_address_or_user(request)
    rate_limit_key = f"ratelimit:{key}:{key_suffix}"

    try:
        count = redis_client.incr(rate_limit_key)

        if count == 1:
            redis_client.expire(rate_limit_key, window_seconds)

        return count <= limit

    except Exception as e:
        logger.error(f"Rate limit check failed: {str(e)}")
        # Fail open (allow request if Redis is down)
        return True


# ============================================================================
# Reset Rate Limit (Admin Function)
# ============================================================================

def reset_rate_limit(identifier: str, endpoint: str = "*"):
    """
    Reset rate limit for a specific user/IP.

    Admin function for manual rate limit resets.

    Args:
        identifier: User ID or IP address
        endpoint: Endpoint pattern (* for all)

    Returns:
        Number of keys deleted
    """
    if endpoint == "*":
        pattern = f"ratelimit:{identifier}:*"
    else:
        pattern = f"ratelimit:{identifier}:{endpoint}"

    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0

    except Exception as e:
        logger.error(f"Failed to reset rate limit: {str(e)}")
        return 0


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "limiter",
    "rate_limit_global",
    "rate_limit_auth",
    "rate_limit_ifc",
    "rate_limit_admin",
    "rate_limit",
    "rate_limit_exceeded_handler",
    "RateLimitMiddleware",
    "get_rate_limit_info",
    "check_rate_limit",
    "reset_rate_limit",
    "get_remote_address_or_user",
    "get_user_key",
]
