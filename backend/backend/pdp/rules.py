"""Policy rules for PDP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import and_

from ..models import User
from .acl_manager import ROLE_PERMISSIONS
from .content_scanner import ContentScanner
from .models import AccessControlList, RateLimit
from .schemas import PolicyRequest, Role


class RoleBasedRule:
    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        user = db_session.query(User).filter(User.id == request.user_id).first()
        if user is None:
            return False, "User not found"
        role = Role(user.role)
        permissions = ROLE_PERMISSIONS.get(role, [])
        if role == Role.ADMIN:
            return True, "Admin has all permissions"
        if request.action in permissions:
            return True, f"Role {role.value} allows {request.action}"
        return False, "Not authorized for action"


class ProjectAccessRule:
    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        user = db_session.query(User).filter(User.id == request.user_id).first()
        if user and user.role == Role.ADMIN.value:
            return True, "Admin has global access"

        project_id = request.context.get("project_id") if request.context else None
        if project_id is None:
            return False, "Project context required"

        acl = (
            db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == request.user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None:
            return False, "No project access"
        if acl.expires_at and acl.expires_at < datetime.utcnow():
            return False, "Access expired"
        return True, "Access granted"


class DataClassificationRule:
    clearance_levels = {
        Role.ADMIN.value: 4,
        Role.DIRECTOR.value: 3,
        Role.ENGINEER.value: 3,
        Role.VIEWER.value: 1,
    }
    classification_levels = {
        "public": 1,
        "internal": 2,
        "confidential": 3,
        "restricted": 4,
    }

    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        classification = (request.context.get("classification") or "public").lower()
        required = self.classification_levels.get(classification, 1)
        user = db_session.query(User).filter(User.id == request.user_id).first()
        if user is None:
            return False, "User not found"
        clearance = self.clearance_levels.get(user.role, 1)
        if clearance >= required:
            return True, "Clearance sufficient"
        return False, "Insufficient clearance"


@dataclass
class TimeBasedRule:
    allowed_hours: List[int]
    allowed_days: List[int]

    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        now = datetime.now()
        if now.hour in self.allowed_hours and now.weekday() in self.allowed_days:
            return True, "Within allowed hours"
        return False, "Outside allowed hours"


class ContentProhibitionRule:
    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        content = request.context.get("content") if request.context else None
        if not content:
            return True, "No content to scan"
        scanner = ContentScanner(db_session)
        result = scanner.scan(content)
        if result.safe:
            return True, "Content scan passed"
        violation = result.violations[0] if result.violations else "Content violation detected"
        return False, violation


@dataclass
class RateLimitRule:
    limit: int
    window_seconds: int

    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        endpoint = request.context.get("endpoint") if request.context else "default"
        record = (
            db_session.query(RateLimit)
            .filter(and_(RateLimit.user_id == request.user_id, RateLimit.endpoint == endpoint))
            .first()
        )
        now = datetime.utcnow()
        if record is None:
            record = RateLimit(
                user_id=request.user_id,
                endpoint=endpoint,
                limit_count=self.limit,
                window_seconds=self.window_seconds,
                current_count=0,
                window_start=now,
            )
            db_session.add(record)
        else:
            if (now - record.window_start).total_seconds() >= record.window_seconds:
                record.current_count = 0
                record.window_start = now

        if record.current_count >= self.limit:
            db_session.commit()
            return False, "Rate limit exceeded"

        record.current_count += 1
        db_session.commit()
        return True, "Within rate limit"


@dataclass
class GeofenceRule:
    allowed_ips: List[str] | None = None
    blocked_ips: List[str] | None = None

    def evaluate(self, request: PolicyRequest, db_session) -> tuple[bool, str]:
        ip_address = request.context.get("ip_address") if request.context else None
        if not ip_address:
            return True, "No IP to check"
        if self.blocked_ips and ip_address in self.blocked_ips:
            return False, "IP is blocked"
        if self.allowed_ips and ip_address not in self.allowed_ips:
            return False, "IP not in allowed list"
        return True, "IP allowed"
