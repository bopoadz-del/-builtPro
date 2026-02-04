"""Hydration API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.backend.db import get_db
from backend.backend.models import User
from backend.hydration.models import WorkspaceSource

router = APIRouter(prefix="/hydration")


def _get_user_id(request: Request) -> int:
    raw = request.headers.get("X-User-ID") or request.headers.get("X-User-Id")
    try:
        return int(raw) if raw is not None else 1
    except ValueError:
        return 1


@router.post("/run-now")
def run_now(payload: dict, request: Request, db: Session = Depends(get_db)):
    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id required")

    sources = (
        db.query(WorkspaceSource)
        .filter(WorkspaceSource.workspace_id == workspace_id, WorkspaceSource.is_enabled.is_(True))
        .all()
    )
    if not sources:
        raise HTTPException(
            status_code=400,
            detail=f"No hydration sources configured for workspace {workspace_id}",
        )

    user_id = _get_user_id(request)
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=403, detail="User not permitted to run hydration")

    return {"status": "queued", "workspace_id": workspace_id}
