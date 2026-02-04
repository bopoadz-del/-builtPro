"""
API endpoints for project schedule analysis.

These endpoints accept schedule files in Primavera P6 (XER), Microsoft Project (MPP, XML)
or related formats and return a structured analysis.  The current implementation
is a placeholder that returns basic file metadata.  Future versions will parse
the schedule content, compute the critical path, resource utilisation and
other useful insights.
"""

from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks

from backend.core.security import get_current_user
from backend.models.auth import User
from backend.api.chat_routes import UPLOAD_DIR  # reuse upload directory
from backend.services.schedule_parser import parse_schedule_file

import uuid

# In-memory job storage for asynchronous analysis results.
# In a production system this should be replaced with a persistent store
# or task queue (e.g. Redis, Celery, database).
analysis_jobs: dict[str, dict[str, Any]] = {}

router = APIRouter()


@router.post("/schedule/analyze", summary="Analyze a project schedule file")
async def analyze_schedule(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload and analyze a project schedule file asynchronously.

    This endpoint saves the uploaded file and schedules a background task
    to parse it and compute schedule metrics. It immediately returns a
    job identifier so the client can poll for results.

    Args:
        background_tasks: FastAPI BackgroundTasks instance.
        file: The uploaded schedule file.
        current_user: Injected current user from the request context.

    Returns:
        A dictionary containing a job ID and status.

    Raises:
        HTTPException: If the file cannot be saved.
    """
    # Create user-specific upload directory if not exists
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(exist_ok=True)

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

    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    # Initialize job status
    analysis_jobs[job_id] = {
        "status": "processing",
        "result": None,
    }

    # Schedule background task to perform analysis
    background_tasks.add_task(_process_schedule_file, job_id, file_path)

    return {"job_id": job_id, "status": "processing"}


def _process_schedule_file(job_id: str, file_path: Path) -> None:
    """Background task to parse and analyze a schedule file.

    This function updates the global `analysis_jobs` dict with the
    final result. It catches exceptions and records them as error
    statuses so clients can inspect failures.

    Args:
        job_id: Identifier of the job to update.
        file_path: Path to the schedule file.
    """
    try:
        result = parse_schedule_file(file_path)
        analysis_jobs[job_id] = {
            "status": "completed",
            "result": result,
        }
    except Exception as exc:
        analysis_jobs[job_id] = {
            "status": "failed",
            "error": str(exc),
        }


@router.get("/schedule/status/{job_id}", summary="Get schedule analysis status")
async def get_analysis_status(job_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Retrieve the status or result of a previously submitted schedule analysis job.

    Args:
        job_id: The identifier returned from the analyze_schedule endpoint.
        current_user: Injected current user from the request context.

    Returns:
        A dictionary containing the job status and, if completed, the analysis result.

    Raises:
        HTTPException: If the job_id is unknown.
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return analysis_jobs[job_id]