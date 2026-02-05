from __future__ import annotations

from datetime import datetime, timedelta
import base64
import json

import logging
from typing import Dict, List, Optional

try:  # pragma: no cover - optional dependency for lightweight deployments
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    np = None  # type: ignore[assignment]

from fastapi import APIRouter, BackgroundTasks, Body, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.redisx.locks import DistributedLock

try:  # pragma: no cover - optional dependency
    import cv2
    _cv2_import_error: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - handled at runtime
    cv2 = None  # type: ignore[assignment]
    _cv2_import_error = exc

try:  # pragma: no cover - optional dependency for lightweight deployments
    from backend.services.progress_tracking_service import (
        ProgressSnapshot,
        ProgressTrackingService,
    )
    _progress_service_import_error: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - handled during runtime
    ProgressTrackingService = None  # type: ignore[assignment]
    ProgressSnapshot = None  # type: ignore[assignment]
    _progress_service_import_error = exc

try:  # pragma: no cover - optional multipart dependency
    import multipart  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled gracefully
    multipart = None  # type: ignore[assignment]

def _file_param(*args, **kwargs):
    if multipart is None:
        return Body(None)
    return File(*args, **kwargs)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/progress", tags=["Progress Tracking"])

if cv2 is None:  # pragma: no cover - diagnostic log for Render deployments
    logger.warning("OpenCV import failed: %s", _cv2_import_error)

if np is None:
    logger.warning("NumPy import failed; progress tracking vision features disabled.")

if ProgressTrackingService is not None and np is not None:
    progress_service: Optional[ProgressTrackingService] = ProgressTrackingService(
        model_path="backend/models/yolov8m.pt",
        custom_model_path="backend/models/construction_yolo.pt",
    )
else:  # pragma: no cover - Render builds may skip CV dependencies
    progress_service = None
    logger.warning(
        "ProgressTrackingService could not be imported: %s",
        _progress_service_import_error,
    )


class AnalyzeRequest(BaseModel):
    location: str = Field(..., description="Site location identifier")
    reference_schedule: Optional[Dict] = Field(
        None,
        description="Expected progress from Primavera schedule",
    )
    compare_with_previous: bool = Field(
        default=True,
        description="Compare with previous snapshot",
    )


class ProgressReportRequest(BaseModel):
    location: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TimeframeComparisonRequest(BaseModel):
    location: str
    timeframe1_start: datetime
    timeframe1_end: datetime
    timeframe2_start: datetime
    timeframe2_end: datetime


class WebhookConfig(BaseModel):
    url: str


class ProgressDataPoint(BaseModel):
    """Progress data for a specific date/period."""
    date: str
    planned_percent: float = Field(..., ge=0, le=100)
    actual_percent: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    """Request to update progress tracking."""
    project_id: str
    location: Optional[str] = None
    current_progress: float = Field(..., ge=0, le=100)
    planned_progress: float = Field(..., ge=0, le=100)
    milestone: Optional[str] = None
    notes: Optional[str] = None
    photo_base64: Optional[str] = None


class ProgressSummary(BaseModel):
    """Progress tracking summary."""
    project_id: str
    current_progress: float
    planned_progress: float
    variance: float
    status: str  # ahead, on_track, behind, critical
    spi: float  # Schedule Performance Index
    trend: str  # improving, stable, declining
    last_updated: str


# In-memory storage for demo
_progress_data: Dict[str, List[Dict]] = {}
_milestones: Dict[str, List[Dict]] = {}


@router.get("/status")
async def get_progress_status():
    """Get progress tracking service status."""
    return {
        "service": "progress_tracking",
        "status": "ok",
        "vision_enabled": progress_service is not None,
        "cv2_available": cv2 is not None,
        "numpy_available": np is not None,
        "tracked_projects": len(_progress_data)
    }


@router.post("/update")
async def update_progress(request: ProgressUpdateRequest):
    """Update progress for a project.
    
    Records current progress against planned schedule and
    calculates performance metrics.
    """
    project_id = request.project_id
    
    # Initialize project tracking if new
    if project_id not in _progress_data:
        _progress_data[project_id] = []
    
    # Calculate metrics
    variance = request.current_progress - request.planned_progress
    spi = request.current_progress / request.planned_progress if request.planned_progress > 0 else 1.0
    
    # Determine status
    if variance >= 2:
        status = "ahead"
    elif variance >= -2:
        status = "on_track"
    elif variance >= -10:
        status = "behind"
    else:
        status = "critical"
    
    # Record data point
    data_point = {
        "timestamp": datetime.now().isoformat(),
        "current_progress": request.current_progress,
        "planned_progress": request.planned_progress,
        "variance": variance,
        "spi": spi,
        "status": status,
        "location": request.location,
        "milestone": request.milestone,
        "notes": request.notes
    }
    
    _progress_data[project_id].append(data_point)
    
    # Calculate trend from recent data
    recent = _progress_data[project_id][-5:]
    if len(recent) >= 3:
        variances = [p["variance"] for p in recent]
        if variances[-1] > variances[0]:
            trend = "improving"
        elif variances[-1] < variances[0] - 2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return {
        "status": "recorded",
        "project_id": project_id,
        "progress": {
            "current": request.current_progress,
            "planned": request.planned_progress,
            "variance": round(variance, 2),
            "spi": round(spi, 3),
            "status": status,
            "trend": trend
        },
        "timestamp": data_point["timestamp"]
    }


@router.get("/summary/{project_id}", response_model=ProgressSummary)
async def get_progress_summary(project_id: str):
    """Get progress summary for a project."""
    if project_id not in _progress_data or not _progress_data[project_id]:
        raise HTTPException(status_code=404, detail=f"No progress data for project: {project_id}")
    
    latest = _progress_data[project_id][-1]
    recent = _progress_data[project_id][-5:]
    
    # Calculate trend
    if len(recent) >= 3:
        variances = [p["variance"] for p in recent]
        if variances[-1] > variances[0]:
            trend = "improving"
        elif variances[-1] < variances[0] - 2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return ProgressSummary(
        project_id=project_id,
        current_progress=latest["current_progress"],
        planned_progress=latest["planned_progress"],
        variance=latest["variance"],
        status=latest["status"],
        spi=latest["spi"],
        trend=trend,
        last_updated=latest["timestamp"]
    )


@router.get("/history/{project_id}")
async def get_progress_history(
    project_id: str,
    limit: int = Query(30, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get progress history for a project."""
    if project_id not in _progress_data:
        return {"project_id": project_id, "history": [], "count": 0}
    
    history = _progress_data[project_id]
    
    # Apply date filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            history = [h for h in history if datetime.fromisoformat(h["timestamp"]) >= start_dt]
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            history = [h for h in history if datetime.fromisoformat(h["timestamp"]) <= end_dt]
        except ValueError:
            pass
    
    # Limit results
    history = history[-limit:]
    
    return {
        "project_id": project_id,
        "history": history,
        "count": len(history)
    }


@router.post("/milestone")
async def record_milestone(
    project_id: str,
    name: str,
    planned_date: str,
    actual_date: Optional[str] = None,
    status: str = "pending",
    notes: Optional[str] = None
):
    """Record a project milestone.
    
    Status can be: pending, completed, delayed, at_risk
    """
    if project_id not in _milestones:
        _milestones[project_id] = []
    
    # Calculate delay if actual date provided
    delay_days = None
    if actual_date:
        try:
            planned_dt = datetime.strptime(planned_date, "%Y-%m-%d")
            actual_dt = datetime.strptime(actual_date, "%Y-%m-%d")
            delay_days = (actual_dt - planned_dt).days
        except ValueError:
            pass
    
    milestone = {
        "name": name,
        "planned_date": planned_date,
        "actual_date": actual_date,
        "status": status,
        "delay_days": delay_days,
        "notes": notes,
        "recorded_at": datetime.now().isoformat()
    }
    
    _milestones[project_id].append(milestone)
    
    return {
        "status": "recorded",
        "milestone": milestone
    }


@router.get("/milestones/{project_id}")
async def get_milestones(project_id: str):
    """Get milestones for a project."""
    milestones = _milestones.get(project_id, [])
    
    # Calculate summary stats
    total = len(milestones)
    completed = len([m for m in milestones if m["status"] == "completed"])
    delayed = len([m for m in milestones if m["status"] == "delayed"])
    at_risk = len([m for m in milestones if m["status"] == "at_risk"])
    
    return {
        "project_id": project_id,
        "milestones": milestones,
        "summary": {
            "total": total,
            "completed": completed,
            "delayed": delayed,
            "at_risk": at_risk,
            "pending": total - completed - delayed - at_risk
        }
    }


@router.post("/compare")
async def compare_progress(
    project_ids: List[str],
    as_of_date: Optional[str] = None
):
    """Compare progress across multiple projects."""
    comparisons = []
    
    for project_id in project_ids:
        if project_id not in _progress_data or not _progress_data[project_id]:
            comparisons.append({
                "project_id": project_id,
                "status": "no_data"
            })
            continue
        
        # Get latest data (or data as of specified date)
        data = _progress_data[project_id]
        if as_of_date:
            try:
                as_of_dt = datetime.fromisoformat(as_of_date)
                data = [d for d in data if datetime.fromisoformat(d["timestamp"]) <= as_of_dt]
            except ValueError:
                pass
        
        if not data:
            comparisons.append({
                "project_id": project_id,
                "status": "no_data_for_date"
            })
            continue
        
        latest = data[-1]
        comparisons.append({
            "project_id": project_id,
            "current_progress": latest["current_progress"],
            "planned_progress": latest["planned_progress"],
            "variance": latest["variance"],
            "spi": latest["spi"],
            "status": latest["status"]
        })
    
    # Rank by performance
    ranked = sorted(
        [c for c in comparisons if "current_progress" in c],
        key=lambda x: x.get("spi", 0),
        reverse=True
    )
    
    return {
        "comparisons": comparisons,
        "ranking": [c["project_id"] for c in ranked],
        "best_performer": ranked[0]["project_id"] if ranked else None,
        "as_of_date": as_of_date or datetime.now().isoformat()
    }


@router.get("/dashboard")
async def get_progress_dashboard():
    """Get dashboard overview of all tracked projects."""
    dashboard = {
        "total_projects": len(_progress_data),
        "projects": [],
        "overall_health": "healthy"
    }
    
    critical_count = 0
    behind_count = 0
    
    for project_id, data in _progress_data.items():
        if not data:
            continue
        
        latest = data[-1]
        project_summary = {
            "project_id": project_id,
            "current_progress": latest["current_progress"],
            "status": latest["status"],
            "spi": latest["spi"],
            "last_updated": latest["timestamp"]
        }
        dashboard["projects"].append(project_summary)
        
        if latest["status"] == "critical":
            critical_count += 1
        elif latest["status"] == "behind":
            behind_count += 1
    
    # Determine overall health
    if critical_count > 0:
        dashboard["overall_health"] = "critical"
    elif behind_count > len(_progress_data) * 0.3:
        dashboard["overall_health"] = "at_risk"
    elif behind_count > 0:
        dashboard["overall_health"] = "warning"
    
    dashboard["summary"] = {
        "critical": critical_count,
        "behind": behind_count,
        "on_track": len([p for p in dashboard["projects"] if p["status"] in ["on_track", "ahead"]])
    }
    
    return dashboard
