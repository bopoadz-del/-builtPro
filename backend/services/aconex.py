"""Aconex connector health checks."""

from __future__ import annotations

import os
from typing import Dict

import httpx


def check_connection() -> Dict[str, object]:
    base_url = os.getenv("ACONEX_BASE_URL")
    api_key = os.getenv("ACONEX_API_KEY")
    if not base_url or not api_key:
        return {
            "service": "aconex",
            "status": "stubbed",
            "details": "Aconex not configured; stubbed transmittals",
        }
    url = f"{base_url}/health"
    try:
        response = httpx.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=5)
        response.raise_for_status()
        return {"service": "aconex", "status": "connected", "details": response.json()}
    except Exception as exc:
        return {
            "service": "aconex",
            "status": "stubbed",
            "error": str(exc),
            "details": "Using stubbed transmittals feed",
        }
