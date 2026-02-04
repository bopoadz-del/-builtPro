"""Progress tracking API stub."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/progress-tracking")


@router.get("/status")
def status():
    return {"status": "ok"}
