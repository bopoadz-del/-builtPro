import os
"""
Chat routes and utilities for the Blank App.

This module defines placeholders for chat-related API endpoints and
constants. The `UPLOAD_DIR` constant is used by other modules to
determine where uploaded files are stored. In a full implementation,
this module would also define routes for sending and receiving chat
messages.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

router = APIRouter()

# Base directory for storing uploaded files. In production this should
# be configurable via an environment variable. Here we default to a
# directory under the project root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
# Ensure the upload directory exists at import time
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Placeholder route (not implemented). Real chat functionality would
# live here.
@router.post("/chat/send", include_in_schema=False)
async def send_chat_message():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Chat functionality is not implemented in this stub.",
    )