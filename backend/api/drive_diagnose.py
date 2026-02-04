"""Drive diagnostics API."""

from __future__ import annotations

from fastapi import APIRouter

from backend.services import google_drive

router = APIRouter(prefix="/drive")


@router.get("/diagnose")
def diagnose_drive():
    if google_drive.drive_stubbed():
        detail = google_drive.drive_service_error() or "Drive service unavailable"
        return {"status": "error", "detail": detail}
    return {"status": "ok", "detail": "Drive service available"}
