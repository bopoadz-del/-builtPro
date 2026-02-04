"""AutoCAD API stub."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/autocad")


@router.get("/takeoff")
def takeoff(file_id: str):
    return {
        "status": "stubbed",
        "result": {
            "file_id": file_id,
            "entities": ["line", "polyline"],
        },
    }
