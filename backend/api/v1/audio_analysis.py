"""
API endpoints for audio transcription.

These endpoints accept audio recordings uploaded by the user and
return a transcript along with basic metadata. The current
implementation uses a placeholder transcription service that does not
perform real speech-to-text; it simply returns a hardcoded message
and audio metadata. Future versions can integrate with actual
transcription engines (e.g. Whisper, Google Speech‑to‑Text).
"""

from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from backend.core.security import get_current_user
from backend.models.auth import User
from backend.api.chat_routes import UPLOAD_DIR  # reuse upload directory
from backend.services.audio_transcription import transcribe_audio_file

router = APIRouter()


@router.post("/audio/transcribe", summary="Transcribe an audio recording")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload and transcribe an audio file.

    Args:
        file: The uploaded audio file.
        current_user: Injected current user from the request context.

    Returns:
        A dictionary containing transcription results and metadata.

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

    # Perform transcription (placeholder)
    try:
        result = transcribe_audio_file(file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to transcribe audio file: {exc}",
        )

    return result