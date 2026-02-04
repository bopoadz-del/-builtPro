"""Event envelope helper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import uuid


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    ts: datetime
    workspace_id: int
    source: str
    payload_json: str
    actor_id: int | None = None
    correlation_id: str | None = None

    @classmethod
    def build(
        cls,
        *,
        event_type: str,
        workspace_id: int,
        source: str,
        payload: dict,
        actor_id: int | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            ts=datetime.utcnow(),
            workspace_id=workspace_id,
            source=source,
            payload_json=json.dumps(payload),
            actor_id=actor_id,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
