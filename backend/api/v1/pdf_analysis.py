"""
API endpoint for PDF file analysis.

This endpoint accepts a PDF file upload, stores it in the user‑specific
uploads directory and returns basic metadata along with a base64‑encoded
thumbnail of the first page. It relies on the ``parse_pdf_file``
function from ``app.services.pdf_parser``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from backend.core.security import get_current_user
from backend.models.auth import User
from backend.api.chat_routes import UPLOAD_DIR
from backend.services.pdf_parser import parse_pdf_file


router = APIRouter()


@router.post("/pdf/analyze", summary="Analyze a PDF document")
async def analyze_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Upload and analyze a PDF document.

    Saves the uploaded PDF into the user’s uploads folder and returns
    metadata including the number of pages and a thumbnail of the
    first page.

    Args:
        file: Uploaded PDF file.
        current_user: Authenticated user context.

    Returns:
        Dictionary containing file metadata, page count and thumbnail.

    Raises:
        HTTPException: If saving or analyzing the file fails.
    """
    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(exist_ok=True)

    file_path = user_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            buffer.write(await file.read())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    try:
        result = parse_pdf_file(file_path)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fnf))
    except RuntimeError as rex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(rex))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return result