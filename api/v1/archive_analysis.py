"""
API endpoints for archive inspection.

These endpoints accept archive files (ZIP, TAR, etc.) uploaded by the user
and return a listing of their contents. The current implementation
supports ZIP and TAR.* formats using Python's standard library and
returns an informative error for other formats. Future iterations may
perform extraction, virus scanning and content-type detection.
"""

from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from backend.core.security import get_current_user
from backend.models.auth import User
from backend.api.chat_routes import UPLOAD_DIR  # reuse upload directory
from backend.services.archive_handler import list_archive_contents

router = APIRouter()


@router.post("/archive/analyze", summary="Analyze an archive file")
async def analyze_archive(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload and inspect an archive file.

    Args:
        file: The uploaded archive file (ZIP, TAR, etc.).
        current_user: Injected current user from the request context.

    Returns:
        A dictionary summarizing the archive contents. The response
        includes the archive type, file count and a list of entries, or
        an error message if the format is unsupported.

    Raises:
        HTTPException: If the file cannot be processed.
    """
    # Create user-specific upload directory if not exists
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file temporarily
    file_path = user_upload_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            buffer.write(await file.read())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # Inspect the archive
    try:
        result = list_archive_contents(file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyze archive file: {exc}",
        )

    return result