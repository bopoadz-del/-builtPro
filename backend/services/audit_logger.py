"""
Audit logging service.

This module provides a simple function to record audit events to the
database.  In production you may extend this to buffer events or
write to an external system (e.g. Kafka or Cloud Logging).
"""

import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.audit import AuditLog


def log_event(db: Session, user_id: Optional[int], action: str, path: str, detail: Optional[Any] = None) -> None:
    """Insert an audit log entry into the database.

    Args:
        db: SQLAlchemy session.
        user_id: ID of the user performing the action, or None.
        action: Short description of the action (e.g. "login", "upload_schedule").
        path: The URL path accessed.
        detail: Optional JSON-serializable context about the event.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        path=path,
        timestamp=datetime.datetime.utcnow(),
        detail=detail,
    )
    db.add(entry)
    db.commit()