"""Forecast Engine API for project schedule and cost predictions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from backend.services.forecast_engine import (
    NUMPY_AVAILABLE,
    RiskLevel,
    ScheduleForecast,
    CostForecast,
    PerformanceMetrics,
    calculate_performance_metrics,
    predict_schedule_delay,
    predict_cost_overrun,
    analyze_trend,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models

class ScheduleForecastRequest(BaseModel):
    """Request for schedule forecast."""
    planned_end_date: str = Field(..., description="Target completion date (YYYY-MM-DD)")
    current_progress: float = Field(..., ge=0, le=100, description="Actual % complete")
    planned_progress: float = Field(..., ge=0, le=100, description="Planned % complete by now")
    project_duration_days: int = Field(default=365, description="Total planned duration")
    elapsed_days: int = Field(default=0, description="Days since project start")
    critical_path_tasks: list[str] = Field(default=[], description="Critical path task names")
    risk_register: list[dict] = Field(default=[], description="List of identified risks")


class CostForecastRequest(BaseModel):
    """Request for cost forecast."""
    budget: float = Field(..., gt=0, description="Total project budget")
    actual_cost: float = Field(..., ge=0, description="Cost incurred to date")
    percent_complete: float = Field(..., ge=0, le=100, description="Work completed %")
    planned_percent: float = Field(default=50, ge=0, le=100, description="Planned % by now")
    committed_costs: float = Field(default=0, ge=0, description="Committed but not spent")
    contingency: float = Field(default=0, ge=0, description="Contingency amount")


class EVMRequest(BaseModel):
    """Request for Earned Value Management calculation."""
    budget_at_completion: float = Field(..., gt=0, description="Total budget (BAC)")
    actual_cost: float = Field(..., ge=0, description="Actual cost (AC)")
    percent_complete: float = Field(..., ge=0, le=100, description="Work completed %")
    planned_percent: float = Field(..., ge=0, le=100, description="Planned % by now")


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis."""
    data_points: list[dict] = Field(..., description="Time series data [{date, value}]")
    metric_key: str = Field(default="value", description="Key for metric value")


class ProjectForecastRequest(BaseModel):
    """Combined request for full project forecast."""
    project_name: str = Field(..., description="Project identifier")
    
    # Schedule data
    planned_end_date: str
    current_progress: float = Field(..., ge=0, le=100)
    planned_progress: float = Field(..., ge=0, le=100)
    project_duration_days: int = 365
    elapsed_days: int = 0
    
    # Cost data
    budget: float
    actual_cost: float
    committed_costs: float = 0
    contingency: float = 0
    
    # Optional
    critical_path_tasks: list[str] = []
    risk_register: list[dict] = []
    historical_projects: list[dict] = []


class ScheduleForecastResponse(BaseModel):
    """Schedule forecast response."""
    original_end_date: str
    forecasted_end_date: str
    delay_days: int
    confidence_level: float
    confidence_range: dict
    probability_on_time: float
    risk_level: str
    critical_path_items: list[str]
    risk_factors: list[dict]
    recommendations: list[str]


class CostForecastResponse(BaseModel):
    """Cost forecast response."""
    original_budget: float
    forecasted_cost: float
    variance: float
    variance_percent: float
    confidence_level: float
    confidence_range: dict
    probability_within_budget: float
    risk_level: str
    cost_drivers: list[dict]
    recommendations: list[str]
    eac_methods: dict


@router.get("/forecast_engine-ping")
async def ping():
    """Health check endpoint."""
    return {
        "service": "forecast_engine",
        "status": "ok",
        "numpy_available": NUMPY_AVAILABLE,
        "capabilities": [
            "schedule_forecast",
            "cost_forecast",
            "evm_analysis",
            "trend_analysis",
            "monte_carlo_simulation"
        ]
    }


@router.post("/forecast/schedule", response_model=ScheduleForecastResponse)
async def forecast_schedule(request: ScheduleForecastRequest):
    """Forecast project schedule completion date.
    
    Uses Schedule Performance Index (SPI) and Monte Carlo simulation
    to predict the likely completion date with confidence ranges.
    """
    try:
        result = predict_schedule_delay({
            "planned_end_date": request.planned_end_date,
            "current_progress": request.current_progress,
            "planned_progress": request.planned_progress,
            "project_duration_days": request.project_duration_days,
            "elapsed_days": request.elapsed_days,
            "critical_path_tasks": request.critical_path_tasks,
            "risk_register": request.risk_register
        })
        
        return ScheduleForecastResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"Schedule forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/cost", response_model=CostForecastResponse)
async def forecast_cost(request: CostForecastRequest):
    """Forecast project cost at completion.
    
    Uses multiple EAC (Estimate at Completion) methods including:
    - EAC = BAC / CPI
    - EAC = AC + (BAC - EV) / CPI
    - EAC = BAC / (CPI × SPI)
    
    Returns weighted average with Monte Carlo confidence ranges.
    """
    try:
        result = predict_cost_overrun({
            "budget": request.budget,
            "actual_cost": request.actual_cost,
            "percent_complete": request.percent_complete,
            "planned_percent": request.planned_percent,
            "committed_costs": request.committed_costs,
            "contingency": request.contingency
        })
        
        return CostForecastResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"Cost forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/evm")
async def calculate_evm(request: EVMRequest):
    """Calculate Earned Value Management metrics.
    
    Returns comprehensive EVM analysis including:
    - Schedule Variance (SV) and Cost Variance (CV)
    - Schedule Performance Index (SPI) and Cost Performance Index (CPI)
    - Estimate at Completion (EAC) and Estimate to Complete (ETC)
    - To Complete Performance Index (TCPI)
    """
    try:
        metrics = calculate_performance_metrics(
            budget_at_completion=request.budget_at_completion,
            actual_cost=request.actual_cost,
            percent_complete=request.percent_complete,
            planned_percent=request.planned_percent
        )
        
        # Add interpretations
        interpretations = []
        
        if metrics.schedule_performance_index < 1.0:
            interpretations.append(f"Project is behind schedule (SPI={metrics.schedule_performance_index:.2f})")
        elif metrics.schedule_performance_index > 1.0:
            interpretations.append(f"Project is ahead of schedule (SPI={metrics.schedule_performance_index:.2f})")
        else:
            interpretations.append("Project is on schedule")
        
        if metrics.cost_performance_index < 1.0:
            interpretations.append(f"Project is over budget (CPI={metrics.cost_performance_index:.2f})")
        elif metrics.cost_performance_index > 1.0:
            interpretations.append(f"Project is under budget (CPI={metrics.cost_performance_index:.2f})")
        else:
            interpretations.append("Project is on budget")
        
        if metrics.to_complete_performance_index > 1.1:
            interpretations.append("Significant improvement needed to meet budget")
        
        return {
            "metrics": metrics.to_dict(),
            "interpretations": interpretations,
            "health_score": min(metrics.schedule_performance_index, metrics.cost_performance_index)
        }
        
    except Exception as e:
        logger.error(f"EVM calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/trend")
async def analyze_project_trend(request: TrendAnalysisRequest):
    """Analyze trend from time series data.
    
    Performs linear regression to identify:
    - Trend direction (improving, stable, declining)
    - Slope and rate of change
    - Forecast for next period
    """
    if not request.data_points:
        raise HTTPException(status_code=400, detail="At least one data point required")
    
    try:
        result = analyze_trend(request.data_points, request.metric_key)
        return result
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/project")
async def full_project_forecast(request: ProjectForecastRequest):
    """Generate comprehensive project forecast combining schedule and cost.
    
    Returns integrated analysis with:
    - Schedule forecast with delay prediction
    - Cost forecast with EAC
    - Combined risk assessment
    - Prioritized recommendations
    """
    try:
        # Schedule forecast
        schedule_result = predict_schedule_delay({
            "planned_end_date": request.planned_end_date,
            "current_progress": request.current_progress,
            "planned_progress": request.planned_progress,
            "project_duration_days": request.project_duration_days,
            "elapsed_days": request.elapsed_days,
            "critical_path_tasks": request.critical_path_tasks,
            "risk_register": request.risk_register
        }, request.historical_projects if request.historical_projects else None)
        
        # Cost forecast
        cost_result = predict_cost_overrun({
            "budget": request.budget,
            "actual_cost": request.actual_cost,
            "percent_complete": request.current_progress,
            "planned_percent": request.planned_progress,
            "committed_costs": request.committed_costs,
            "contingency": request.contingency
        }, request.historical_projects if request.historical_projects else None)
        
        # EVM metrics
        evm_metrics = calculate_performance_metrics(
            budget_at_completion=request.budget,
            actual_cost=request.actual_cost,
            percent_complete=request.current_progress,
            planned_percent=request.planned_progress
        )
        
        # Combined risk level
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        combined_risk_score = (risk_scores[schedule_result.risk_level] + risk_scores[cost_result.risk_level]) / 2
        
        if combined_risk_score >= 3.5:
            overall_risk = RiskLevel.CRITICAL
        elif combined_risk_score >= 2.5:
            overall_risk = RiskLevel.HIGH
        elif combined_risk_score >= 1.5:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Health score (0-100)
        spi = evm_metrics.schedule_performance_index
        cpi = evm_metrics.cost_performance_index
        health_score = min(100, int((spi * 50) + (cpi * 50)))
        
        # Combined recommendations (prioritized)
        all_recommendations = []
        for rec in schedule_result.recommendations:
            all_recommendations.append({"type": "schedule", "recommendation": rec})
        for rec in cost_result.recommendations:
            all_recommendations.append({"type": "cost", "recommendation": rec})
        
        return {
            "project_name": request.project_name,
            "forecast_date": datetime.now().isoformat(),
            "schedule_forecast": schedule_result.to_dict(),
            "cost_forecast": cost_result.to_dict(),
            "evm_metrics": evm_metrics.to_dict(),
            "overall_assessment": {
                "risk_level": overall_risk.value,
                "health_score": health_score,
                "health_status": "healthy" if health_score >= 80 else "at_risk" if health_score >= 60 else "critical",
                "probability_success": round((schedule_result.probability_on_time + cost_result.probability_within_budget) / 2, 2)
            },
            "recommendations": all_recommendations[:10]
        }
        
    except Exception as e:
        logger.error(f"Project forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/what-if")
async def what_if_analysis(
    base_request: ProjectForecastRequest = Body(...),
    scenarios: list[dict] = Body(..., description="List of scenario modifications")
):
    """Run what-if scenario analysis.
    
    Compare multiple scenarios against the baseline to evaluate
    different recovery strategies or risk impacts.
    
    Example scenarios:
    - {"name": "Add resources", "current_progress": 55}
    - {"name": "Reduce scope", "budget": 900000}
    """
    if not scenarios:
        raise HTTPException(status_code=400, detail="At least one scenario required")
    
    if len(scenarios) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 scenarios allowed")
    
    try:
        # Calculate baseline
        baseline_schedule = predict_schedule_delay({
            "planned_end_date": base_request.planned_end_date,
            "current_progress": base_request.current_progress,
            "planned_progress": base_request.planned_progress,
            "project_duration_days": base_request.project_duration_days,
            "elapsed_days": base_request.elapsed_days,
        })
        
        baseline_cost = predict_cost_overrun({
            "budget": base_request.budget,
            "actual_cost": base_request.actual_cost,
            "percent_complete": base_request.current_progress,
            "planned_percent": base_request.planned_progress,
        })
        
        # Calculate each scenario
        scenario_results = []
        
        for scenario in scenarios:
            name = scenario.get("name", f"Scenario {len(scenario_results) + 1}")
            
            # Merge scenario with baseline
            schedule_data = {
                "planned_end_date": scenario.get("planned_end_date", base_request.planned_end_date),
                "current_progress": scenario.get("current_progress", base_request.current_progress),
                "planned_progress": scenario.get("planned_progress", base_request.planned_progress),
                "project_duration_days": scenario.get("project_duration_days", base_request.project_duration_days),
                "elapsed_days": scenario.get("elapsed_days", base_request.elapsed_days),
            }
            
            cost_data = {
                "budget": scenario.get("budget", base_request.budget),
                "actual_cost": scenario.get("actual_cost", base_request.actual_cost),
                "percent_complete": scenario.get("current_progress", base_request.current_progress),
                "planned_percent": scenario.get("planned_progress", base_request.planned_progress),
            }
            
            scenario_schedule = predict_schedule_delay(schedule_data)
            scenario_cost = predict_cost_overrun(cost_data)
            
            # Calculate deltas
            delay_delta = scenario_schedule.delay_days - baseline_schedule.delay_days
            cost_delta = scenario_cost.variance - baseline_cost.variance
            
            scenario_results.append({
                "name": name,
                "inputs": scenario,
                "schedule": {
                    "forecasted_end_date": scenario_schedule.forecasted_end_date,
                    "delay_days": scenario_schedule.delay_days,
                    "delay_delta": delay_delta,
                    "risk_level": scenario_schedule.risk_level.value
                },
                "cost": {
                    "forecasted_cost": round(scenario_cost.forecasted_cost, 2),
                    "variance": round(scenario_cost.variance, 2),
                    "variance_delta": round(cost_delta, 2),
                    "risk_level": scenario_cost.risk_level.value
                },
                "improvement": delay_delta < 0 or cost_delta < 0
            })
        
        return {
            "baseline": {
                "schedule": {
                    "forecasted_end_date": baseline_schedule.forecasted_end_date,
                    "delay_days": baseline_schedule.delay_days
                },
                "cost": {
                    "forecasted_cost": round(baseline_cost.forecasted_cost, 2),
                    "variance": round(baseline_cost.variance, 2)
                }
            },
            "scenarios": scenario_results,
            "best_scenario": min(scenario_results, key=lambda s: s["schedule"]["delay_days"] + s["cost"]["variance"] / base_request.budget * 100)["name"] if scenario_results else None
        }
        
    except Exception as e:
        logger.error(f"What-if analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
