"""Anomaly Detection API for construction project monitoring."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.anomaly_detector import detect_anomalies

logger = logging.getLogger(__name__)
router = APIRouter()


# In-memory storage for demo (would be database in production)
_alert_history: list[dict] = []
_thresholds: dict[str, dict] = {
    "schedule": {"variance_tolerance": 5.0, "delay_days_warning": 7, "delay_days_critical": 14},
    "cost": {"tolerance_pct": 5.0, "overrun_warning": 10.0, "overrun_critical": 20.0},
    "risk": {"threshold": 0.7, "critical_threshold": 0.9},
    "safety": {"incident_warning": 1, "incident_critical": 3},
    "quality": {"defect_warning": 3, "defect_critical": 5}
}


class DataPoint(BaseModel):
    """Single telemetry data point."""
    timestamp: Optional[str] = None
    
    # Schedule metrics
    progress_percent: Optional[float] = Field(None, ge=0, le=100)
    expected_progress_percent: Optional[float] = Field(None, ge=0, le=100)
    schedule_delay_days: Optional[float] = None
    milestone: Optional[str] = None
    
    # Cost metrics
    planned_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    
    # Risk metrics
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    risk_threshold: Optional[float] = Field(None, ge=0, le=1)
    risk_drivers: list[str] = []
    section: Optional[str] = None
    
    # Safety metrics
    incidents: Optional[int] = Field(None, ge=0)
    safety_incidents: Optional[int] = Field(None, ge=0)
    
    # Quality metrics
    defects: Optional[int] = Field(None, ge=0)
    punch_items: Optional[int] = Field(None, ge=0)
    
    # Notes
    notes: Optional[str] = None


class DetectionRequest(BaseModel):
    """Request for anomaly detection."""
    data_stream: list[DataPoint] = Field(..., min_length=1)
    project_id: Optional[str] = None
    include_low_severity: bool = True


class AnomalyResponse(BaseModel):
    """Single anomaly finding."""
    type: str
    severity: str
    message: str
    timestamp: Optional[str]
    context: dict


class DetectionResponse(BaseModel):
    """Anomaly detection response."""
    anomalies: list[AnomalyResponse]
    total_count: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    detection_timestamp: str


class ThresholdUpdate(BaseModel):
    """Threshold configuration update."""
    category: str = Field(..., description="Category: schedule, cost, risk, safety, quality")
    thresholds: dict = Field(..., description="Threshold values to update")


class AlertRule(BaseModel):
    """Custom alert rule definition."""
    name: str
    condition_type: str = Field(..., description="gt, lt, eq, between")
    metric: str
    threshold_value: float
    severity: str = Field(default="medium", description="low, medium, high, critical")
    enabled: bool = True


@router.get("/anomaly_detector-ping")
async def ping():
    """Health check endpoint."""
    return {
        "service": "anomaly_detector",
        "status": "ok",
        "supported_types": ["risk", "schedule", "cost", "safety", "quality"],
        "severities": ["low", "medium", "high", "critical"]
    }


@router.post("/anomalies/detect", response_model=DetectionResponse)
async def detect_project_anomalies(request: DetectionRequest):
    """Detect anomalies in project telemetry data.
    
    Analyzes multiple data points across categories:
    - **Risk**: Score exceeding thresholds
    - **Schedule**: Progress variance, milestone delays
    - **Cost**: Budget overruns
    - **Safety**: Incident counts, near misses
    - **Quality**: Defects, punch list items
    
    Returns prioritized findings sorted by severity.
    """
    try:
        # Convert Pydantic models to dicts
        data_stream = [dp.dict(exclude_none=True) for dp in request.data_stream]
        
        # Run detection
        findings = detect_anomalies(data_stream)
        
        # Filter low severity if requested
        if not request.include_low_severity:
            findings = [f for f in findings if f["severity"] != "low"]
        
        # Count by severity and type
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}
        
        for finding in findings:
            sev = finding.get("severity", "medium")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            ftype = finding.get("type", "other")
            by_type[ftype] = by_type.get(ftype, 0) + 1
        
        # Store in history
        if request.project_id:
            for finding in findings:
                _alert_history.append({
                    **finding,
                    "project_id": request.project_id,
                    "detected_at": datetime.now().isoformat()
                })
        
        return DetectionResponse(
            anomalies=[
                AnomalyResponse(
                    type=f["type"],
                    severity=f["severity"],
                    message=f["message"],
                    timestamp=f.get("timestamp"),
                    context=f.get("context", {})
                )
                for f in findings
            ],
            total_count=len(findings),
            by_severity=by_severity,
            by_type=by_type,
            detection_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies/detect-single")
async def detect_single_point(data_point: DataPoint, project_id: Optional[str] = None):
    """Detect anomalies in a single data point.
    
    Convenience endpoint for real-time monitoring when processing
    one data point at a time (e.g., from IoT sensors or webhooks).
    """
    try:
        findings = detect_anomalies([data_point.dict(exclude_none=True)])
        
        if project_id:
            for finding in findings:
                _alert_history.append({
                    **finding,
                    "project_id": project_id,
                    "detected_at": datetime.now().isoformat()
                })
        
        return {
            "has_anomalies": len(findings) > 0,
            "anomalies": findings,
            "highest_severity": findings[0]["severity"] if findings else None
        }
        
    except Exception as e:
        logger.error(f"Single point detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/thresholds")
async def get_thresholds():
    """Get current anomaly detection thresholds."""
    return {
        "thresholds": _thresholds,
        "description": {
            "schedule": {
                "variance_tolerance": "Acceptable % deviation from planned progress",
                "delay_days_warning": "Days late to trigger warning",
                "delay_days_critical": "Days late to trigger critical alert"
            },
            "cost": {
                "tolerance_pct": "Acceptable % cost variance",
                "overrun_warning": "% overrun for warning",
                "overrun_critical": "% overrun for critical"
            },
            "risk": {
                "threshold": "Risk score to trigger medium alert",
                "critical_threshold": "Risk score for critical alert"
            },
            "safety": {
                "incident_warning": "Incidents for warning",
                "incident_critical": "Incidents for critical"
            },
            "quality": {
                "defect_warning": "Defects for warning",
                "defect_critical": "Defects for critical"
            }
        }
    }


@router.put("/anomalies/thresholds")
async def update_thresholds(update: ThresholdUpdate):
    """Update anomaly detection thresholds.
    
    Allows customization of sensitivity for each category.
    """
    if update.category not in _thresholds:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category: {update.category}. Valid: {list(_thresholds.keys())}"
        )
    
    _thresholds[update.category].update(update.thresholds)
    
    return {
        "status": "updated",
        "category": update.category,
        "new_thresholds": _thresholds[update.category]
    }


@router.get("/anomalies/history")
async def get_alert_history(
    project_id: Optional[str] = None,
    severity: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get historical anomaly alerts.
    
    Retrieve past alerts with optional filtering by project,
    severity, type, and time range.
    """
    cutoff = datetime.now() - timedelta(hours=hours)
    
    filtered = _alert_history
    
    # Apply filters
    if project_id:
        filtered = [a for a in filtered if a.get("project_id") == project_id]
    
    if severity:
        filtered = [a for a in filtered if a.get("severity") == severity]
    
    if anomaly_type:
        filtered = [a for a in filtered if a.get("type") == anomaly_type]
    
    # Filter by time
    filtered = [
        a for a in filtered 
        if a.get("detected_at") and datetime.fromisoformat(a["detected_at"]) >= cutoff
    ]
    
    # Sort by detection time (newest first) and limit
    filtered.sort(key=lambda a: a.get("detected_at", ""), reverse=True)
    filtered = filtered[:limit]
    
    return {
        "alerts": filtered,
        "total": len(filtered),
        "time_range": {
            "from": cutoff.isoformat(),
            "to": datetime.now().isoformat()
        }
    }


@router.delete("/anomalies/history")
async def clear_alert_history(
    project_id: Optional[str] = None,
    older_than_hours: int = Query(24, ge=1)
):
    """Clear alert history.
    
    Optionally filter by project and age.
    """
    global _alert_history
    
    cutoff = datetime.now() - timedelta(hours=older_than_hours)
    original_count = len(_alert_history)
    
    if project_id:
        _alert_history = [
            a for a in _alert_history
            if not (a.get("project_id") == project_id and 
                   a.get("detected_at") and 
                   datetime.fromisoformat(a["detected_at"]) < cutoff)
        ]
    else:
        _alert_history = [
            a for a in _alert_history
            if a.get("detected_at") and datetime.fromisoformat(a["detected_at"]) >= cutoff
        ]
    
    cleared = original_count - len(_alert_history)
    
    return {
        "status": "cleared",
        "alerts_removed": cleared,
        "remaining": len(_alert_history)
    }


@router.post("/anomalies/simulate")
async def simulate_anomalies(
    days: int = Query(7, ge=1, le=30, description="Days to simulate"),
    project_id: str = Query(default="demo_project"),
    anomaly_rate: float = Query(0.3, ge=0, le=1, description="Probability of anomaly per day")
):
    """Generate simulated project data with anomalies for testing.
    
    Creates realistic telemetry data with configurable anomaly rate
    for demo and testing purposes.
    """
    import random
    
    simulated_data = []
    base_date = datetime.now() - timedelta(days=days)
    
    base_progress = 30.0  # Starting progress
    base_cost = 1000000  # Base planned cost
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        
        # Normal progression
        planned_progress = base_progress + (day * 2.0)  # 2% per day planned
        actual_progress = planned_progress + random.uniform(-3, 3)  # Small variance
        
        planned_cost = base_cost * (planned_progress / 100)
        actual_cost = planned_cost * random.uniform(0.95, 1.05)
        
        # Introduce anomalies randomly
        has_anomaly = random.random() < anomaly_rate
        
        data_point = {
            "timestamp": current_date.isoformat(),
            "progress_percent": min(100, max(0, actual_progress)),
            "expected_progress_percent": min(100, planned_progress),
            "planned_cost": planned_cost,
            "actual_cost": actual_cost,
            "section": f"Zone-{random.randint(1, 5)}",
            "notes": ""
        }
        
        if has_anomaly:
            anomaly_type = random.choice(["schedule", "cost", "risk", "safety", "quality"])
            
            if anomaly_type == "schedule":
                data_point["schedule_delay_days"] = random.randint(3, 21)
                data_point["milestone"] = f"Milestone-{random.randint(1, 10)}"
            elif anomaly_type == "cost":
                data_point["actual_cost"] = planned_cost * random.uniform(1.1, 1.3)
            elif anomaly_type == "risk":
                data_point["risk_score"] = random.uniform(0.75, 0.95)
                data_point["risk_drivers"] = random.sample(
                    ["Weather", "Supply chain", "Labor shortage", "Design changes", "Permits"],
                    k=random.randint(1, 3)
                )
            elif anomaly_type == "safety":
                data_point["incidents"] = random.randint(1, 3)
                data_point["notes"] = random.choice(["near miss", "PPE non-compliance", "minor injury"])
            elif anomaly_type == "quality":
                data_point["defects"] = random.randint(2, 8)
                data_point["notes"] = random.choice(["rework required", "failed inspection", "non-conformance"])
        
        simulated_data.append(data_point)
    
    # Run detection on simulated data
    findings = detect_anomalies(simulated_data)
    
    return {
        "project_id": project_id,
        "simulation_period": {
            "start": base_date.isoformat(),
            "end": datetime.now().isoformat(),
            "days": days
        },
        "data_points_generated": len(simulated_data),
        "anomaly_rate": anomaly_rate,
        "anomalies_detected": len(findings),
        "findings": findings,
        "sample_data": simulated_data[:5]  # Return first 5 for reference
    }


@router.get("/anomalies/dashboard")
async def get_anomaly_dashboard(project_id: Optional[str] = None):
    """Get anomaly dashboard summary.
    
    Provides overview statistics for monitoring dashboards.
    """
    # Filter by project if specified
    alerts = _alert_history
    if project_id:
        alerts = [a for a in alerts if a.get("project_id") == project_id]
    
    # Calculate time periods
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    alerts_24h = [a for a in alerts if a.get("detected_at") and datetime.fromisoformat(a["detected_at"]) >= last_24h]
    alerts_7d = [a for a in alerts if a.get("detected_at") and datetime.fromisoformat(a["detected_at"]) >= last_7d]
    
    # Count by severity
    severity_24h = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in alerts_24h:
        sev = a.get("severity", "medium")
        severity_24h[sev] = severity_24h.get(sev, 0) + 1
    
    # Count by type
    type_7d = {}
    for a in alerts_7d:
        t = a.get("type", "other")
        type_7d[t] = type_7d.get(t, 0) + 1
    
    # Recent critical alerts
    critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
    critical_alerts.sort(key=lambda a: a.get("detected_at", ""), reverse=True)
    
    return {
        "summary": {
            "total_alerts_24h": len(alerts_24h),
            "total_alerts_7d": len(alerts_7d),
            "critical_count": severity_24h["critical"],
            "high_count": severity_24h["high"]
        },
        "severity_breakdown_24h": severity_24h,
        "type_breakdown_7d": type_7d,
        "recent_critical": critical_alerts[:5],
        "health_status": "critical" if severity_24h["critical"] > 0 else "warning" if severity_24h["high"] > 2 else "healthy",
        "last_updated": now.isoformat()
    }
