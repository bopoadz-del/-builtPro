"""
Audit log model for the Blank App.

This module defines a SQLAlchemy ORM model for audit logging.  Each
record captures the user performing an action, the route or path
accessed, a timestamp and optional detail.  Enterprise applications
use audit logs for compliance and monitoring.
"""

import datetime
from typing import Optional, Any

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base


# In a larger application you might import a shared Base from
# app.core.database or a central models package.  Here we declare
# our own Base for demonstration.  When integrating into an existing
# database module, adjust accordingly.
Base = declarative_base()


class AuditLog(Base):
    """ORM model for audit log entries."""

    __tablename__ = "audit_logs"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: Optional[int] = Column(Integer, index=True, nullable=True)
    action: str = Column(String, nullable=False)
    path: str = Column(String, nullable=False)
    timestamp: datetime.datetime = Column(DateTime, default=datetime.datetime.utcnow)
    detail: Optional[Any] = Column(JSON)