"""Parsing API stub."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/parsing")


@router.get("/extract")
def extract(file_id: str):
    return {
        "status": "ok",
        "content": f"Stub data for Drive file {file_id}",
    }
