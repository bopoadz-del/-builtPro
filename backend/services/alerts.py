"""Alert delivery helpers."""

from __future__ import annotations

import os
from typing import Any, Dict

import requests


def _post_webhook(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(url, json=payload, timeout=5)
    if response.status_code >= 400:
        return {"status": "error", "error": response.text}
    return {"status": "sent"}


def send_alert(message: str) -> Dict[str, Any]:
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    teams_url = os.getenv("TEAMS_WEBHOOK_URL")

    if not slack_url and not teams_url:
        return {"status": "skipped", "reason": "No webhook configured"}

    targets: Dict[str, Any] = {}
    if slack_url:
        targets["slack"] = _post_webhook(slack_url, {"text": message})
    if teams_url:
        targets["teams"] = _post_webhook(teams_url, {"text": message})

    failures = [target for target in targets.values() if target["status"] == "error"]
    if failures and len(failures) == len(targets):
        return {"status": "error", "reason": "All webhook deliveries failed", "targets": targets}
    if failures:
        return {
            "status": "sent",
            "reason": "One or more webhook deliveries failed",
            "targets": targets,
        }
    return {"status": "sent", "targets": targets}
