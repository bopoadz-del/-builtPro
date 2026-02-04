"""Event projector implementation."""

from __future__ import annotations

import json

from sqlalchemy import and_

from .envelope import EventEnvelope
from .models import EventLog, WorkspaceStateProjection


class EventProjector:
    @staticmethod
    def apply(event: EventEnvelope, db_session) -> bool:
        existing = db_session.query(EventLog).filter(EventLog.event_id == event.event_id).first()
        if existing is not None:
            return False

        log = EventLog(
            event_id=event.event_id,
            event_type=event.event_type,
            ts=event.ts,
            workspace_id=event.workspace_id,
            actor_id=event.actor_id,
            correlation_id=event.correlation_id,
            source=event.source,
            payload_json=json.loads(event.payload_json),
        )
        db_session.add(log)

        if event.event_type == "hydration.completed":
            payload = json.loads(event.payload_json)
            projection = (
                db_session.query(WorkspaceStateProjection)
                .filter(WorkspaceStateProjection.workspace_id == event.workspace_id)
                .first()
            )
            if projection is None:
                projection = WorkspaceStateProjection(workspace_id=event.workspace_id)
                db_session.add(projection)
            projection.last_hydration_job_id = payload.get("job_id")
            projection.last_hydration_at = event.ts

        db_session.commit()
        return True
