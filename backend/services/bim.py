"""BIM connector health checks."""

from __future__ import annotations

import os
from typing import Dict

import httpx


def check_connection() -> Dict[str, object]:
    base_url = os.getenv("BIM_BASE_URL")
    token = os.getenv("BIM_AUTH_TOKEN")
    if not base_url or not token:
        return {"service": "bim", "status": "stubbed", "details": "BIM stub active"}
    url = f"{base_url}/health"
    try:
        response = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
        response.raise_for_status()
        return {"service": "bim", "status": "connected", "details": response.json()}
    except Exception as exc:
        return {"service": "bim", "status": "error", "error": str(exc)}
