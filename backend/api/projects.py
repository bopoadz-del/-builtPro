"""Projects API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/projects")


@router.get("/scan-drive")
def scan_drive():
    now = datetime.utcnow().isoformat()
    projects = [
        {"name": "Drive Project A", "path": "/Drive/A", "last_modified": now, "source": "stubbed"},
        {"name": "Drive Project B", "path": "/Drive/B", "last_modified": now, "source": "stubbed"},
    ]
    return {
        "status": "stubbed",
        "detail": "Drive scanning stubbed",
        "projects": projects,
    }
