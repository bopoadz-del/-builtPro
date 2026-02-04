"""Connector status API."""

from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter

from backend.services import aconex, bim, google_drive, primavera, vision

router = APIRouter(prefix="/connectors")


def _health_check(url: str) -> Dict[str, str]:
    try:
        response = httpx.get(url, timeout=5)
        response.raise_for_status()
        return {"status": "connected"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def bim_status() -> Dict[str, Any]:
    return bim.check_connection()


def primavera_status() -> Dict[str, Any]:
    return primavera.check_connection()


def aconex_status() -> Dict[str, Any]:
    return aconex.check_connection()


def vision_status() -> Dict[str, Any]:
    return vision.check_connection()


def _drive_status() -> Dict[str, Any]:
    if google_drive.drive_credentials_available() and not google_drive.drive_stubbed():
        return {"status": "connected"}
    if google_drive.drive_service_error():
        return {"status": "error", "detail": google_drive.drive_service_error()}
    if google_drive.drive_credentials_available():
        return {"status": "stubbed"}
    return {"status": "error"}


def _service_status(env_name: str) -> Dict[str, Any]:
    url = os.getenv(env_name)
    if not url:
        return {"status": "unconfigured"}
    return _health_check(url)


@router.get("/list")
def list_connectors():
    onedrive = _service_status("ONEDRIVE_HEALTH_URL")
    teams = _service_status("TEAMS_HEALTH_URL")
    power_bi = _service_status("POWER_BI_HEALTH_URL")

    return {
        "google_drive": _drive_status(),
        "onedrive": onedrive,
        "teams": teams,
        "power_bi": power_bi,
        "bim": bim_status(),
        "p6": primavera_status(),
        "aconex": aconex_status(),
        "vision": vision_status(),
        "photo": {"service": "photo", "status": "error"},
    }
