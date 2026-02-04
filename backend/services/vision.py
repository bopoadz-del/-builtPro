"""Vision connector health checks."""

from __future__ import annotations

import os
from typing import Dict

import httpx


def check_connection() -> Dict[str, object]:
    base_url = os.getenv("VISION_BASE_URL")
    api_key = os.getenv("VISION_API_KEY")
    if not base_url or not api_key:
        return {"service": "vision", "status": "stubbed", "details": "Vision stub active"}
    url = f"{base_url}/health"
    try:
        response = httpx.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=5)
        response.raise_for_status()
        return {"service": "vision", "status": "connected", "details": response.json()}
    except Exception as exc:
        return {"service": "vision", "status": "error", "error": str(exc)}
