"""Alert websocket helpers (stub)."""

from __future__ import annotations

from typing import Any, Dict, List

_ALERT_QUEUE: List[Dict[str, Any]] = []


def enqueue_alert(payload: Dict[str, Any]) -> None:
    _ALERT_QUEUE.append(payload)


def get_alerts() -> List[Dict[str, Any]]:
    return list(_ALERT_QUEUE)
