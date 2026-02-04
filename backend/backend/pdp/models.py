"""Database models for PDP."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.sqlite import JSON

from ..db import Base


class AccessControlList(Base):
    __tablename__ = "pdp_acl"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    role = Column(String(50), nullable=False)
    permissions_json = Column(JSON, nullable=False, default=list)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    granted_by = Column(Integer, nullable=True)

    @property
    def permissions(self) -> list[str]:
        return list(self.permissions_json or [])


class Policy(Base):
    __tablename__ = "pdp_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    policy_type = Column(String(50), nullable=False)
    rules_json = Column(JSON, nullable=False, default=dict)
    enabled = Column(Integer, default=1)
    priority = Column(Integer, default=100)


class PDPAuditLog(Base):
    __tablename__ = "pdp_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    decision = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)


class RateLimit(Base):
    __tablename__ = "pdp_rate_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    endpoint = Column(String(100), nullable=False, index=True)
    limit_count = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    current_count = Column(Integer, nullable=False, default=0)
    window_start = Column(DateTime, default=datetime.utcnow, nullable=False)
