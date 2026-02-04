"""Events API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.backend.db import get_db
from backend.events.models import EventLog

router = APIRouter(prefix="/events")


@router.get("/global")
def list_events(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(EventLog).order_by(EventLog.ts.desc()).limit(limit).all()
    return [
        {
            "event_id": log.event_id,
            "event_type": log.event_type,
            "ts": log.ts.isoformat(),
            "workspace_id": log.workspace_id,
            "actor_id": log.actor_id,
            "correlation_id": log.correlation_id,
            "source": log.source,
            "payload": log.payload_json,
        }
        for log in logs
    ]


@router.get("/workspace/{workspace_id}")
def list_workspace_events(workspace_id: int, limit: int = 50, db: Session = Depends(get_db)):
    logs = (
        db.query(EventLog)
        .filter(EventLog.workspace_id == workspace_id)
        .order_by(EventLog.ts.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "event_id": log.event_id,
            "event_type": log.event_type,
            "ts": log.ts.isoformat(),
            "workspace_id": log.workspace_id,
            "actor_id": log.actor_id,
            "correlation_id": log.correlation_id,
            "source": log.source,
            "payload": log.payload_json,
        }
        for log in logs
    ]
