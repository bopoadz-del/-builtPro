"""Primavera P6 connector health checks."""

from __future__ import annotations

import os
from typing import Dict

import httpx


def check_connection() -> Dict[str, object]:
    base_url = os.getenv("PRIMAVERA_BASE_URL")
    username = os.getenv("PRIMAVERA_USERNAME")
    password = os.getenv("PRIMAVERA_PASSWORD")
    if not base_url or not username or not password:
        return {
            "service": "p6",
            "status": "stubbed",
            "details": "Primavera not configured; using stubbed activities",
        }
    url = f"{base_url}/health"
    try:
        response = httpx.get(url, auth=(username, password), timeout=5)
        response.raise_for_status()
        return {"service": "p6", "status": "connected", "details": response.json()}
    except Exception as exc:
        return {
            "service": "p6",
            "status": "stubbed",
            "error": str(exc),
            "details": "Using stubbed activities feed",
        }
