"""Rate limiter implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Tuple

from sqlalchemy import and_

from .models import RateLimit

RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "default": {"limit": 10, "window_seconds": 60},
    "chat": {"limit": 5, "window_seconds": 60},
    "export": {"limit": 2, "window_seconds": 300},
}


class RateLimiter:
    def __init__(self, db_session) -> None:
        self.db_session = db_session

    def _get_config(self, endpoint: str) -> Dict[str, int]:
        return RATE_LIMITS.get(endpoint, RATE_LIMITS["default"])

    def _is_expired(self, record: RateLimit) -> bool:
        return datetime.utcnow() - record.window_start >= timedelta(seconds=record.window_seconds)

    def _reset_record(self, record: RateLimit, endpoint: str) -> None:
        config = self._get_config(endpoint)
        record.limit_count = config["limit"]
        record.window_seconds = config["window_seconds"]
        record.current_count = 0
        record.window_start = datetime.utcnow()

    def check_limit(self, user_id: int, endpoint: str) -> Tuple[bool, int]:
        record = (
            self.db_session.query(RateLimit)
            .filter(and_(RateLimit.user_id == user_id, RateLimit.endpoint == endpoint))
            .first()
        )
        if record is None:
            config = self._get_config(endpoint)
            record = RateLimit(
                user_id=user_id,
                endpoint=endpoint,
                limit_count=config["limit"],
                window_seconds=config["window_seconds"],
                current_count=0,
                window_start=datetime.utcnow(),
            )
            self.db_session.add(record)
            self.db_session.commit()
        elif self._is_expired(record):
            self._reset_record(record, endpoint)
            self.db_session.commit()

        remaining = max(record.limit_count - record.current_count, 0)
        allowed = remaining > 0
        return allowed, remaining

    def increment(self, user_id: int, endpoint: str) -> int:
        record = (
            self.db_session.query(RateLimit)
            .filter(and_(RateLimit.user_id == user_id, RateLimit.endpoint == endpoint))
            .first()
        )
        if record is None:
            config = self._get_config(endpoint)
            record = RateLimit(
                user_id=user_id,
                endpoint=endpoint,
                limit_count=config["limit"],
                window_seconds=config["window_seconds"],
                current_count=0,
                window_start=datetime.utcnow(),
            )
            self.db_session.add(record)
        elif self._is_expired(record):
            self._reset_record(record, endpoint)

        record.current_count += 1
        self.db_session.commit()
        return record.current_count

    def reset_window(self, user_id: int, endpoint: str) -> bool:
        record = (
            self.db_session.query(RateLimit)
            .filter(and_(RateLimit.user_id == user_id, RateLimit.endpoint == endpoint))
            .first()
        )
        if record is None:
            return False
        self._reset_record(record, endpoint)
        self.db_session.commit()
        return True

    def get_limits(self, user_id: int) -> Dict[str, Dict[str, int | float | str]]:
        limits: Dict[str, Dict[str, int | float | str]] = {}
        records = self.db_session.query(RateLimit).filter(RateLimit.user_id == user_id).all()
        for record in records:
            remaining = max(record.limit_count - record.current_count, 0)
            reset_in_seconds = max(
                int(record.window_seconds - (datetime.utcnow() - record.window_start).total_seconds()),
                0,
            )
            limits[record.endpoint] = {
                "limit": record.limit_count,
                "current": record.current_count,
                "remaining": remaining,
                "reset_in_seconds": reset_in_seconds,
                "window_seconds": record.window_seconds,
                "window_start": record.window_start.isoformat(),
            }
        return limits

    def get_time_until_reset(self, user_id: int, endpoint: str) -> int:
        record = (
            self.db_session.query(RateLimit)
            .filter(and_(RateLimit.user_id == user_id, RateLimit.endpoint == endpoint))
            .first()
        )
        if record is None:
            return 0
        elapsed = (datetime.utcnow() - record.window_start).total_seconds()
        return max(int(record.window_seconds - elapsed), 0)

    def cleanup_expired_windows(self, hours: int = 24) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        records = self.db_session.query(RateLimit).filter(RateLimit.window_start < cutoff).all()
        count = len(records)
        for record in records:
            self.db_session.delete(record)
        self.db_session.commit()
        return count
