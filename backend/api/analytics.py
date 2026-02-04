"""Analytics API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/analytics")


@router.get("")
def list_analytics():
    now = datetime.utcnow().isoformat()
    entries = [
        {"id": "log-1", "action": "view", "user_id": "user-1", "message_id": "msg-1", "timestamp": now},
        {"id": "log-2", "action": "edit", "user_id": "user-2", "message_id": "msg-2", "timestamp": now},
    ]
    return entries
