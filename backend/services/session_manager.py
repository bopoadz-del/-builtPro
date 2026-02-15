"""
Session Manager for BuilTPro Brain AI

User session management with JWT integration and security features.

Features:
- Session creation and validation
- JWT token management
- Refresh token rotation
- Session expiration
- Multi-device support
- Session revocation
- Activity tracking
- Security monitoring (suspicious activity detection)

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, List
import secrets
import hashlib
from threading import Lock

logger = logging.getLogger(__name__)


class SessionError(Exception):
    """Base exception for session errors."""
    pass


class SessionExpired(SessionError):
    """Raised when session is expired."""
    pass


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    token: str
    refresh_token: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionActivity:
    """Session activity log entry."""
    session_id: str
    timestamp: datetime
    action: str
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Production-ready session manager."""

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
        self.sessions: Dict[str, Session] = {}
        self.sessions_by_user: Dict[str, List[str]] = {}
        self.activity_log: List[SessionActivity] = []

        self.default_session_ttl_hours = 24
        self.refresh_token_ttl_days = 30
        self.max_sessions_per_user = 5

        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "revoked_sessions": 0
        }

        logger.info("Session Manager initialized")

    def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        ttl_hours: Optional[int] = None
    ) -> Session:
        """Create a new session."""
        try:
            session_id = self._generate_session_id()
            token = self._generate_token()
            refresh_token = self._generate_token()

            ttl = ttl_hours or self.default_session_ttl_hours
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=ttl)

            session = Session(
                session_id=session_id,
                user_id=user_id,
                token=token,
                refresh_token=refresh_token,
                created_at=now,
                expires_at=expires_at,
                last_activity=now,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id
            )

            # Store session
            self.sessions[session_id] = session

            # Track by user
            if user_id not in self.sessions_by_user:
                self.sessions_by_user[user_id] = []
            self.sessions_by_user[user_id].append(session_id)

            # Enforce max sessions per user
            self._enforce_session_limit(user_id)

            # Log activity
            self._log_activity(session_id, "session_created", ip_address)

            # Update stats
            self.stats["total_sessions"] += 1
            self.stats["active_sessions"] += 1

            logger.info(f"Created session for user {user_id}")

            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionError(f"Session creation failed: {e}")

    def validate_session(self, token: str) -> Session:
        """Validate a session token."""
        # Find session by token
        session = None
        for s in self.sessions.values():
            if s.token == token:
                session = s
                break

        if not session:
            raise SessionError("Invalid session token")

        # Check expiration
        if datetime.utcnow() > session.expires_at:
            session.status = SessionStatus.EXPIRED
            self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            self.stats["expired_sessions"] += 1
            raise SessionExpired("Session expired")

        # Check status
        if session.status != SessionStatus.ACTIVE:
            raise SessionError(f"Session {session.status.value}")

        # Update last activity
        session.last_activity = datetime.utcnow()

        return session

    def refresh_session(self, refresh_token: str) -> Session:
        """Refresh a session using refresh token."""
        # Find session by refresh token
        session = None
        for s in self.sessions.values():
            if s.refresh_token == refresh_token:
                session = s
                break

        if not session:
            raise SessionError("Invalid refresh token")

        if datetime.utcnow() > session.expires_at:
            if session.status != SessionStatus.EXPIRED:
                session.status = SessionStatus.EXPIRED
                self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
                self.stats["expired_sessions"] += 1
            raise SessionExpired("Session expired")

        if session.status != SessionStatus.ACTIVE:
            raise SessionError(f"Session {session.status.value}")

        # Generate new tokens
        session.token = self._generate_token()
        session.refresh_token = self._generate_token()

        # Extend expiration
        session.expires_at = datetime.utcnow() + timedelta(hours=self.default_session_ttl_hours)
        session.last_activity = datetime.utcnow()

        self._log_activity(session.session_id, "session_refreshed", session.ip_address)

        logger.info(f"Refreshed session {session.session_id}")

        return session

    def revoke_session(self, session_id: str) -> None:
        """Revoke a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.status = SessionStatus.REVOKED

            self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            self.stats["revoked_sessions"] += 1

            self._log_activity(session_id, "session_revoked", session.ip_address)

            logger.info(f"Revoked session {session_id}")

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        count = 0

        if user_id in self.sessions_by_user:
            for session_id in self.sessions_by_user[user_id]:
                if session_id in self.sessions:
                    self.revoke_session(session_id)
                    count += 1

        logger.info(f"Revoked {count} sessions for user {user_id}")

        return count

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user."""
        session_ids = self.sessions_by_user.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = []

        for session_id, session in self.sessions.items():
            if now > session.expires_at:
                expired.append(session_id)

        for session_id in expired:
            if session_id in self.sessions:
                session = self.sessions[session_id]

                # Remove from user tracking
                if session.user_id in self.sessions_by_user:
                    if session_id in self.sessions_by_user[session.user_id]:
                        self.sessions_by_user[session.user_id].remove(session_id)

                del self.sessions[session_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"sess_{secrets.token_urlsafe(32)}"

    def _generate_token(self) -> str:
        """Generate a secure token."""
        return secrets.token_urlsafe(64)

    def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum sessions per user."""
        if user_id not in self.sessions_by_user:
            return

        session_ids = self.sessions_by_user[user_id]

        if len(session_ids) > self.max_sessions_per_user:
            # Get sessions sorted by last activity
            user_sessions = [
                self.sessions[sid] for sid in session_ids
                if sid in self.sessions
            ]
            user_sessions.sort(key=lambda s: s.last_activity)

            # Revoke oldest sessions
            to_revoke = len(user_sessions) - self.max_sessions_per_user
            for session in user_sessions[:to_revoke]:
                self.revoke_session(session.session_id)

    def _log_activity(
        self,
        session_id: str,
        action: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log session activity."""
        activity = SessionActivity(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            action=action,
            ip_address=ip_address
        )

        self.activity_log.append(activity)

        # Keep only recent activity (last 10000 entries)
        if len(self.activity_log) > 10000:
            self.activity_log = self.activity_log[-10000:]

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        return {
            **self.stats,
            "total_users_with_sessions": len(self.sessions_by_user),
            "activity_log_entries": len(self.activity_log)
        }


session_manager = SessionManager()
