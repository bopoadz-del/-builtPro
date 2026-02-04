"""
API endpoints for CAD file analysis.

This module defines an endpoint to upload a CAD or 3D model file and
receive basic metadata about the file. It uses the ``parse_cad_file``
function from ``app.services.cad_parser`` to perform the analysis. In a
future version this endpoint could offload intensive processing to
background jobs and return detailed geometry or design insights.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from backend.core.security import get_current_user
from backend.models.auth import User
from backend.api.chat_routes import UPLOAD_DIR  # base directory for uploads
from backend.services.cad_parser import parse_cad_file


router = APIRouter()


@router.post("/cad/analyze", summary="Analyze a CAD file")
async def analyze_cad(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Upload and analyze a CAD or 3D model file.

    The file is saved into a user‑specific directory under ``UPLOAD_DIR`` and
    then passed to ``parse_cad_file`` for analysis. Currently only simple
    metadata is returned.

    Args:
        file: The uploaded CAD file from the request body.
        current_user: The authenticated user making the request.

    Returns:
        A dictionary containing metadata about the file and a message.

    Raises:
        HTTPException: If the file cannot be saved.
    """
    # Create a directory for this user if it does not exist
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(exist_ok=True)

    # Save the uploaded file to disk
    file_path = user_upload_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            buffer.write(await file.read())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # Perform analysis
    try:
        result = parse_cad_file(file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze CAD file: {exc}",
        )

    return result