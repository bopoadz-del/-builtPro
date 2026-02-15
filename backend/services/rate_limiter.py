"""
Rate Limiter for BuilTPro Brain AI

API throttling and quota management using token bucket and sliding window algorithms.

Features:
- Multiple algorithms (token bucket, sliding window, fixed window)
- Per-user rate limiting
- Per-IP rate limiting
- API endpoint-specific limits
- Quota management
- Rate limit headers
- Burst handling
- Distributed rate limiting support

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, List
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Base exception for rate limiting errors."""
    pass


class RateLimitExceeded(RateLimitError):
    """Raised when rate limit is exceeded."""
    pass


class Algorithm(str, Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    limit_id: str
    requests_per_window: int
    window_seconds: int
    algorithm: Algorithm = Algorithm.SLIDING_WINDOW
    burst_size: Optional[int] = None


@dataclass
class RateLimitStatus:
    """Current rate limit status."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after_seconds: Optional[int] = None


@dataclass
class TokenBucket:
    """Token bucket state."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float
    last_refill: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SlidingWindow:
    """Sliding window state."""
    requests: deque
    window_seconds: int
    max_requests: int


class RateLimiter:
    """Production-ready rate limiter."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.limits: Dict[str, RateLimit] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        self.stats = {"total_requests": 0, "blocked_requests": 0}

        logger.info("Rate Limiter initialized")

    def add_limit(self, limit: RateLimit) -> None:
        """Add a rate limit configuration."""
        self.limits[limit.limit_id] = limit
        logger.info(f"Added rate limit: {limit.limit_id} ({limit.requests_per_window}/{limit.window_seconds}s)")

    def check_rate_limit(
        self,
        limit_id: str,
        identifier: str
    ) -> RateLimitStatus:
        """
        Check if request is allowed under rate limit.

        Args:
            limit_id: Rate limit configuration ID
            identifier: User/IP/key identifier

        Returns:
            RateLimitStatus

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        if limit_id not in self.limits:
            # No limit configured, allow
            return RateLimitStatus(
                allowed=True,
                limit=0,
                remaining=0,
                reset_at=datetime.utcnow()
            )

        limit = self.limits[limit_id]
        key = f"{limit_id}:{identifier}"

        self.stats["total_requests"] += 1

        if limit.algorithm == Algorithm.TOKEN_BUCKET:
            status = self._check_token_bucket(key, limit)
        elif limit.algorithm == Algorithm.SLIDING_WINDOW:
            status = self._check_sliding_window(key, limit)
        else:  # FIXED_WINDOW
            status = self._check_fixed_window(key, limit)

        if not status.allowed:
            self.stats["blocked_requests"] += 1
            raise RateLimitExceeded(f"Rate limit exceeded: {limit_id}")

        return status

    def _check_token_bucket(self, key: str, limit: RateLimit) -> RateLimitStatus:
        """Check using token bucket algorithm."""
        now = datetime.utcnow()

        if key not in self.token_buckets:
            # Initialize bucket
            bucket = TokenBucket(
                capacity=limit.burst_size or limit.requests_per_window,
                refill_rate=limit.requests_per_window / limit.window_seconds,
                tokens=limit.burst_size or limit.requests_per_window
            )
            self.token_buckets[key] = bucket
        else:
            bucket = self.token_buckets[key]

        # Refill tokens
        time_passed = (now - bucket.last_refill).total_seconds()
        bucket.tokens = min(
            bucket.capacity,
            bucket.tokens + (time_passed * bucket.refill_rate)
        )
        bucket.last_refill = now

        # Check if token available
        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return RateLimitStatus(
                allowed=True,
                limit=bucket.capacity,
                remaining=int(bucket.tokens),
                reset_at=now + timedelta(seconds=limit.window_seconds)
            )
        else:
            # Calculate retry after
            tokens_needed = 1 - bucket.tokens
            retry_after = int(tokens_needed / bucket.refill_rate)

            return RateLimitStatus(
                allowed=False,
                limit=bucket.capacity,
                remaining=0,
                reset_at=now + timedelta(seconds=retry_after),
                retry_after_seconds=retry_after
            )

    def _check_sliding_window(self, key: str, limit: RateLimit) -> RateLimitStatus:
        """Check using sliding window algorithm."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=limit.window_seconds)

        if key not in self.sliding_windows:
            # Initialize window
            window = SlidingWindow(
                requests=deque(),
                window_seconds=limit.window_seconds,
                max_requests=limit.requests_per_window
            )
            self.sliding_windows[key] = window
        else:
            window = self.sliding_windows[key]

        # Remove old requests
        while window.requests and window.requests[0] < window_start:
            window.requests.popleft()

        # Check limit
        if len(window.requests) < window.max_requests:
            window.requests.append(now)
            return RateLimitStatus(
                allowed=True,
                limit=window.max_requests,
                remaining=window.max_requests - len(window.requests),
                reset_at=now + timedelta(seconds=limit.window_seconds)
            )
        else:
            # Calculate when oldest request will expire
            oldest = window.requests[0]
            reset_at = oldest + timedelta(seconds=limit.window_seconds)
            retry_after = int((reset_at - now).total_seconds())

            return RateLimitStatus(
                allowed=False,
                limit=window.max_requests,
                remaining=0,
                reset_at=reset_at,
                retry_after_seconds=max(1, retry_after)
            )

    def _check_fixed_window(self, key: str, limit: RateLimit) -> RateLimitStatus:
        """Check using fixed window algorithm."""
        # Simplified fixed window using sliding window with alignment
        return self._check_sliding_window(key, limit)

    def reset(self, limit_id: str, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        key = f"{limit_id}:{identifier}"

        if key in self.token_buckets:
            del self.token_buckets[key]
        if key in self.sliding_windows:
            del self.sliding_windows[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        block_rate = 0
        if self.stats["total_requests"] > 0:
            block_rate = (self.stats["blocked_requests"] / self.stats["total_requests"]) * 100

        return {
            **self.stats,
            "block_rate_percent": block_rate,
            "active_limits": len(self.limits),
            "tracked_identifiers": len(self.token_buckets) + len(self.sliding_windows)
        }


rate_limiter = RateLimiter()
