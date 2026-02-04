"""Google Drive integration helpers."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Optional

_drive_service: Any | None = None
_service_ready = False
_service_error: str | None = None
MediaIoBaseUpload: Any | None = None


def _load_google_clients() -> tuple[Any, Any, Any] | None:
    if "googleapiclient.discovery" in sys.modules:
        import googleapiclient.discovery as discovery
    else:
        if importlib.util.find_spec("googleapiclient.discovery") is None:
            return None
        import googleapiclient.discovery as discovery

    if "googleapiclient.http" in sys.modules:
        import googleapiclient.http as http
    else:
        if importlib.util.find_spec("googleapiclient.http") is None:
            return None
        import googleapiclient.http as http

    if "google.oauth2.service_account" in sys.modules:
        import google.oauth2.service_account as service_account
    else:
        if importlib.util.find_spec("google.oauth2.service_account") is None:
            return None
        import google.oauth2.service_account as service_account

    return discovery, http, service_account


def drive_credentials_available() -> bool:
    credential_path = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if not credential_path:
        return False
    return Path(credential_path).exists()


def drive_service_error() -> str | None:
    return _service_error


def drive_stubbed() -> bool:
    return not drive_credentials_available() or _service_error is not None


def _initialise_service() -> Any:
    global _drive_service, _service_ready, _service_error

    clients = _load_google_clients()
    if clients is None:
        _service_error = "google client libraries are unavailable"
        raise RuntimeError(_service_error)

    discovery, _, service_account = clients
    credential_path = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if not credential_path:
        _service_error = "Google service account not configured"
        raise RuntimeError(_service_error)

    credentials = service_account.Credentials.from_service_account_file(
        credential_path,
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    try:
        _drive_service = discovery.build("drive", "v3", credentials=credentials)
    except Exception as exc:
        _service_error = str(exc)
        raise
    _service_ready = True
    _service_error = None
    return _drive_service


def get_drive_service() -> Any:
    global _drive_service, _service_ready
    if _service_ready and _drive_service is not None:
        return _drive_service
    return _initialise_service()


def upload_to_drive(file_obj: Any) -> str:
    global _service_error

    try:
        service = get_drive_service()
    except Exception as exc:
        _service_error = str(exc)
        return "stubbed-upload-id"

    clients = _load_google_clients()
    if clients is None:
        _service_error = "google client libraries are unavailable"
        return "stubbed-upload-id"

    _, http, _ = clients
    upload_cls = MediaIoBaseUpload or http.MediaIoBaseUpload
    media = upload_cls(file_obj, mimetype="application/octet-stream", resumable=False)
    response = service.files().create(body={"name": "upload"}, media_body=media, fields="id").execute()
    return response.get("id", "stubbed-upload-id")
