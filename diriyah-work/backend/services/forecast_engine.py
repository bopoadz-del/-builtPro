"""Forecast Engine Service for Construction Project Predictions.

Provides schedule and cost forecasting using statistical methods and Monte Carlo simulation.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import numpy for better calculations
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False
    logger.info("NumPy not available - using basic statistics")


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class ScheduleForecast:
    """Schedule completion forecast result."""
    original_end_date: str
    forecasted_end_date: str
    delay_days: int
    confidence_level: float  # 0-1
    confidence_range_low: str  # Optimistic date
    confidence_range_high: str  # Pessimistic date
    probability_on_time: float  # 0-1
    risk_level: RiskLevel
    critical_path_items: list[str] = field(default_factory=list)
    risk_factors: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "original_end_date": self.original_end_date,
            "forecasted_end_date": self.forecasted_end_date,
            "delay_days": self.delay_days,
            "confidence_level": round(self.confidence_level, 2),
            "confidence_range": {
                "optimistic": self.confidence_range_low,
                "pessimistic": self.confidence_range_high
            },
            "probability_on_time": round(self.probability_on_time, 2),
            "risk_level": self.risk_level.value,
            "critical_path_items": self.critical_path_items,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations
        }


@dataclass
class CostForecast:
    """Cost at completion forecast result."""
    original_budget: float
    forecasted_cost: float
    variance: float
    variance_percent: float
    confidence_level: float
    confidence_range_low: float
    confidence_range_high: float
    probability_within_budget: float
    risk_level: RiskLevel
    cost_drivers: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    eac_methods: dict = field(default_factory=dict)  # Different EAC calculation methods
    
    def to_dict(self) -> dict:
        return {
            "original_budget": round(self.original_budget, 2),
            "forecasted_cost": round(self.forecasted_cost, 2),
            "variance": round(self.variance, 2),
            "variance_percent": round(self.variance_percent, 1),
            "confidence_level": round(self.confidence_level, 2),
            "confidence_range": {
                "optimistic": round(self.confidence_range_low, 2),
                "pessimistic": round(self.confidence_range_high, 2)
            },
            "probability_within_budget": round(self.probability_within_budget, 2),
            "risk_level": self.risk_level.value,
            "cost_drivers": self.cost_drivers,
            "recommendations": self.recommendations,
            "eac_methods": {k: round(v, 2) for k, v in self.eac_methods.items()}
        }


@dataclass
class PerformanceMetrics:
    """Earned Value Management metrics."""
    # Base values
    budget_at_completion: float  # BAC
    actual_cost: float  # AC
    earned_value: float  # EV
    planned_value: float  # PV
    
    # Variances
    schedule_variance: float  # SV = EV - PV
    cost_variance: float  # CV = EV - AC
    schedule_variance_percent: float  # SV%
    cost_variance_percent: float  # CV%
    
    # Indices
    schedule_performance_index: float  # SPI = EV / PV
    cost_performance_index: float  # CPI = EV / AC
    
    # Forecasts
    estimate_at_completion: float  # EAC
    estimate_to_complete: float  # ETC
    variance_at_completion: float  # VAC = BAC - EAC
    to_complete_performance_index: float  # TCPI
    
    def to_dict(self) -> dict:
        return {
            "budget_at_completion": round(self.budget_at_completion, 2),
            "actual_cost": round(self.actual_cost, 2),
            "earned_value": round(self.earned_value, 2),
            "planned_value": round(self.planned_value, 2),
            "schedule_variance": round(self.schedule_variance, 2),
            "cost_variance": round(self.cost_variance, 2),
            "schedule_variance_percent": round(self.schedule_variance_percent, 1),
            "cost_variance_percent": round(self.cost_variance_percent, 1),
            "schedule_performance_index": round(self.schedule_performance_index, 3),
            "cost_performance_index": round(self.cost_performance_index, 3),
            "estimate_at_completion": round(self.estimate_at_completion, 2),
            "estimate_to_complete": round(self.estimate_to_complete, 2),
            "variance_at_completion": round(self.variance_at_completion, 2),
            "to_complete_performance_index": round(self.to_complete_performance_index, 3)
        }


def _calculate_std_dev(values: list[float]) -> float:
    """Calculate standard deviation."""
    if NUMPY_AVAILABLE:
        return float(np.std(values)) if values else 0.0
    
    if not values or len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _calculate_mean(values: list[float]) -> float:
    """Calculate mean."""
    if NUMPY_AVAILABLE:
        return float(np.mean(values)) if values else 0.0
    return sum(values) / len(values) if values else 0.0


def _monte_carlo_simulation(
    base_value: float,
    std_dev: float,
    iterations: int = 1000,
    bias: float = 0.0
) -> tuple[float, float, float]:
    """Run Monte Carlo simulation for forecasting.
    
    Returns: (mean, p10_optimistic, p90_pessimistic)
    """
    if NUMPY_AVAILABLE:
        samples = np.random.normal(base_value + bias, std_dev, iterations)
        return float(np.mean(samples)), float(np.percentile(samples, 10)), float(np.percentile(samples, 90))
    
    # Fallback to basic random sampling
    samples = []
    for _ in range(iterations):
        sample = random.gauss(base_value + bias, std_dev)
        samples.append(sample)
    
    samples.sort()
    mean = sum(samples) / len(samples)
    p10 = samples[int(len(samples) * 0.1)]
    p90 = samples[int(len(samples) * 0.9)]
    
    return mean, p10, p90


def calculate_performance_metrics(
    budget_at_completion: float,
    actual_cost: float,
    percent_complete: float,
    planned_percent: float
) -> PerformanceMetrics:
    """Calculate Earned Value Management metrics.
    
    Args:
        budget_at_completion: Total project budget (BAC)
        actual_cost: Money spent to date (AC)
        percent_complete: Actual work completed (0-100)
        planned_percent: Planned work to date (0-100)
    
    Returns:
        PerformanceMetrics with all EVM calculations
    """
    # Convert percentages to fractions
    pct_complete = percent_complete / 100
    pct_planned = planned_percent / 100
    
    # Calculate base values
    earned_value = budget_at_completion * pct_complete  # EV
    planned_value = budget_at_completion * pct_planned  # PV
    
    # Variances
    schedule_variance = earned_value - planned_value  # SV
    cost_variance = earned_value - actual_cost  # CV
    
    schedule_variance_percent = (schedule_variance / planned_value * 100) if planned_value > 0 else 0
    cost_variance_percent = (cost_variance / earned_value * 100) if earned_value > 0 else 0
    
    # Performance indices
    spi = earned_value / planned_value if planned_value > 0 else 1.0
    cpi = earned_value / actual_cost if actual_cost > 0 else 1.0
    
    # Forecasts - using CPI method
    eac = budget_at_completion / cpi if cpi > 0 else budget_at_completion
    etc = eac - actual_cost
    vac = budget_at_completion - eac
    
    # To Complete Performance Index
    remaining_work = budget_at_completion - earned_value
    remaining_budget = budget_at_completion - actual_cost
    tcpi = remaining_work / remaining_budget if remaining_budget > 0 else float('inf')
    
    return PerformanceMetrics(
        budget_at_completion=budget_at_completion,
        actual_cost=actual_cost,
        earned_value=earned_value,
        planned_value=planned_value,
        schedule_variance=schedule_variance,
        cost_variance=cost_variance,
        schedule_variance_percent=schedule_variance_percent,
        cost_variance_percent=cost_variance_percent,
        schedule_performance_index=spi,
        cost_performance_index=cpi,
        estimate_at_completion=eac,
        estimate_to_complete=etc,
        variance_at_completion=vac,
        to_complete_performance_index=tcpi
    )


def predict_schedule_delay(
    schedule_data: dict,
    historical_performance: Optional[list[dict]] = None
) -> ScheduleForecast:
    """Predict project schedule completion.
    
    Args:
        schedule_data: Current project schedule data containing:
            - planned_end_date: Original target date (YYYY-MM-DD)
            - current_progress: Actual % complete (0-100)
            - planned_progress: Expected % complete by now (0-100)
            - project_duration_days: Total planned duration
            - elapsed_days: Days since project start
            - critical_path_tasks: List of critical path items
            - risk_register: List of identified risks
        historical_performance: Optional list of past performance data
    
    Returns:
        ScheduleForecast with predictions and recommendations
    """
    # Extract inputs with defaults
    planned_end = schedule_data.get("planned_end_date", "")
    current_progress = float(schedule_data.get("current_progress", 50))
    planned_progress = float(schedule_data.get("planned_progress", 50))
    duration_days = int(schedule_data.get("project_duration_days", 365))
    elapsed_days = int(schedule_data.get("elapsed_days", duration_days // 2))
    critical_tasks = schedule_data.get("critical_path_tasks", [])
    risk_register = schedule_data.get("risk_register", [])
    
    # Parse planned end date
    try:
        planned_end_dt = datetime.strptime(planned_end, "%Y-%m-%d") if planned_end else datetime.now() + timedelta(days=duration_days - elapsed_days)
    except ValueError:
        planned_end_dt = datetime.now() + timedelta(days=duration_days - elapsed_days)
    
    # Calculate Schedule Performance Index
    spi = current_progress / planned_progress if planned_progress > 0 else 1.0
    
    # Calculate remaining work and time
    remaining_progress = 100 - current_progress
    remaining_days_planned = duration_days - elapsed_days
    
    # Forecast remaining duration based on SPI
    if spi > 0:
        forecasted_remaining = remaining_days_planned / spi
    else:
        forecasted_remaining = remaining_days_planned * 2  # Assume worst case
    
    # Calculate delay
    delay_days = int(forecasted_remaining - remaining_days_planned)
    
    # Historical performance adjustment
    historical_variance = 0.0
    if historical_performance:
        delays = [p.get("actual_delay_days", 0) for p in historical_performance if p.get("actual_delay_days")]
        if delays:
            historical_variance = _calculate_std_dev(delays)
            avg_delay = _calculate_mean(delays)
            delay_days = int(delay_days + avg_delay * 0.3)  # Weight historical by 30%
    
    # Calculate forecasted end date
    forecasted_end_dt = planned_end_dt + timedelta(days=delay_days)
    
    # Monte Carlo for confidence range
    base_delay = float(delay_days)
    std_dev = max(historical_variance, duration_days * 0.05)  # At least 5% duration as std dev
    
    _, optimistic_delay, pessimistic_delay = _monte_carlo_simulation(base_delay, std_dev)
    
    optimistic_dt = planned_end_dt + timedelta(days=int(optimistic_delay))
    pessimistic_dt = planned_end_dt + timedelta(days=int(pessimistic_delay))
    
    # Calculate probability of on-time completion
    if delay_days <= 0:
        prob_on_time = 0.85
    elif delay_days < duration_days * 0.05:
        prob_on_time = 0.65
    elif delay_days < duration_days * 0.1:
        prob_on_time = 0.35
    else:
        prob_on_time = 0.15
    
    # Determine risk level
    if spi >= 0.95:
        risk_level = RiskLevel.LOW
    elif spi >= 0.85:
        risk_level = RiskLevel.MEDIUM
    elif spi >= 0.75:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL
    
    # Compile risk factors
    risk_factors = []
    if spi < 1.0:
        risk_factors.append({
            "factor": "Schedule Performance",
            "description": f"SPI of {spi:.2f} indicates behind schedule",
            "impact": "high" if spi < 0.85 else "medium"
        })
    
    for risk in risk_register[:5]:
        risk_factors.append({
            "factor": risk.get("name", "Identified Risk"),
            "description": risk.get("description", ""),
            "impact": risk.get("impact", "medium")
        })
    
    # Generate recommendations
    recommendations = []
    if spi < 0.9:
        recommendations.append("Consider schedule acceleration options (overtime, additional resources)")
    if spi < 0.8:
        recommendations.append("Conduct critical path analysis to identify recovery opportunities")
    if delay_days > 30:
        recommendations.append("Initiate formal schedule recovery plan with stakeholder communication")
    if len(critical_tasks) > 5:
        recommendations.append("Review critical path for potential fast-tracking or crashing opportunities")
    if not recommendations:
        recommendations.append("Maintain current performance to achieve on-time completion")
    
    return ScheduleForecast(
        original_end_date=planned_end_dt.strftime("%Y-%m-%d"),
        forecasted_end_date=forecasted_end_dt.strftime("%Y-%m-%d"),
        delay_days=max(0, delay_days),
        confidence_level=0.75,
        confidence_range_low=optimistic_dt.strftime("%Y-%m-%d"),
        confidence_range_high=pessimistic_dt.strftime("%Y-%m-%d"),
        probability_on_time=prob_on_time,
        risk_level=risk_level,
        critical_path_items=critical_tasks[:10] if critical_tasks else ["No critical path data provided"],
        risk_factors=risk_factors,
        recommendations=recommendations
    )


def predict_cost_overrun(
    cost_data: dict,
    historical_performance: Optional[list[dict]] = None
) -> CostForecast:
    """Predict project cost at completion.
    
    Args:
        cost_data: Current cost data containing:
            - budget: Original budget (BAC)
            - actual_cost: Money spent to date (AC)
            - percent_complete: Work completed (0-100)
            - planned_percent: Planned work by now (0-100)
            - committed_costs: Committed but not spent
            - contingency: Contingency amount
        historical_performance: Optional list of past cost performance
    
    Returns:
        CostForecast with predictions and recommendations
    """
    # Extract inputs
    budget = float(cost_data.get("budget", 1000000))
    actual_cost = float(cost_data.get("actual_cost", 0))
    percent_complete = float(cost_data.get("percent_complete", 50))
    planned_percent = float(cost_data.get("planned_percent", 50))
    committed = float(cost_data.get("committed_costs", 0))
    contingency = float(cost_data.get("contingency", budget * 0.1))
    
    # Calculate EVM metrics
    metrics = calculate_performance_metrics(budget, actual_cost, percent_complete, planned_percent)
    
    # Multiple EAC methods
    cpi = metrics.cost_performance_index
    spi = metrics.schedule_performance_index
    
    eac_methods = {
        "eac_cpi": budget / cpi if cpi > 0 else budget * 1.5,  # EAC = BAC / CPI
        "eac_ac_plus_etc": actual_cost + (budget - metrics.earned_value) / cpi if cpi > 0 else actual_cost + (budget - metrics.earned_value),  # EAC = AC + (BAC - EV) / CPI
        "eac_composite": budget / (cpi * spi) if cpi > 0 and spi > 0 else budget * 1.5,  # EAC = BAC / (CPI * SPI)
    }
    
    # Use weighted average of methods
    forecasted_cost = sum(eac_methods.values()) / len(eac_methods)
    
    # Historical adjustment
    historical_variance = 0.0
    if historical_performance:
        overruns = [p.get("cost_overrun_percent", 0) for p in historical_performance]
        if overruns:
            historical_variance = _calculate_std_dev(overruns) * budget / 100
            avg_overrun = _calculate_mean(overruns)
            forecasted_cost *= (1 + avg_overrun * 0.002)  # Small adjustment based on history
    
    # Monte Carlo for confidence range
    std_dev = max(historical_variance, budget * 0.08)  # At least 8% of budget
    
    _, optimistic_cost, pessimistic_cost = _monte_carlo_simulation(forecasted_cost, std_dev)
    
    # Calculate variance
    variance = forecasted_cost - budget
    variance_percent = (variance / budget * 100) if budget > 0 else 0
    
    # Probability within budget
    if variance <= 0:
        prob_within_budget = 0.85
    elif variance < contingency:
        prob_within_budget = 0.55
    elif variance < budget * 0.1:
        prob_within_budget = 0.30
    else:
        prob_within_budget = 0.10
    
    # Determine risk level
    if cpi >= 0.98:
        risk_level = RiskLevel.LOW
    elif cpi >= 0.90:
        risk_level = RiskLevel.MEDIUM
    elif cpi >= 0.80:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL
    
    # Cost drivers
    cost_drivers = []
    if cpi < 1.0:
        cost_drivers.append({
            "driver": "Cost Performance",
            "description": f"CPI of {cpi:.2f} indicates cost inefficiency",
            "impact_amount": actual_cost - metrics.earned_value
        })
    
    if committed > budget * 0.1:
        cost_drivers.append({
            "driver": "Committed Costs",
            "description": f"Outstanding commitments of {committed:,.0f}",
            "impact_amount": committed
        })
    
    # Recommendations
    recommendations = []
    if cpi < 0.95:
        recommendations.append("Review cost control procedures and identify areas for efficiency")
    if cpi < 0.85:
        recommendations.append("Conduct value engineering workshop to identify savings opportunities")
    if variance > contingency:
        recommendations.append("Request contingency increase or scope reduction to maintain budget")
    if committed > budget - actual_cost:
        recommendations.append("Review committed costs for cancellation or renegotiation opportunities")
    if not recommendations:
        recommendations.append("Continue monitoring to maintain cost performance")
    
    return CostForecast(
        original_budget=budget,
        forecasted_cost=forecasted_cost,
        variance=variance,
        variance_percent=variance_percent,
        confidence_level=0.75,
        confidence_range_low=optimistic_cost,
        confidence_range_high=pessimistic_cost,
        probability_within_budget=prob_within_budget,
        risk_level=risk_level,
        cost_drivers=cost_drivers,
        recommendations=recommendations,
        eac_methods=eac_methods
    )


def analyze_trend(
    data_points: list[dict],
    metric_key: str = "value"
) -> dict:
    """Analyze trend from time series data.
    
    Args:
        data_points: List of dicts with 'date' and metric_key
        metric_key: Key for the metric value
    
    Returns:
        Trend analysis results
    """
    if not data_points or len(data_points) < 2:
        return {
            "direction": TrendDirection.STABLE.value,
            "slope": 0.0,
            "confidence": 0.0,
            "forecast_next": None
        }
    
    values = [float(p.get(metric_key, 0)) for p in data_points]
    
    # Simple linear regression
    n = len(values)
    x = list(range(n))
    
    mean_x = sum(x) / n
    mean_y = sum(values) / n
    
    numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator > 0 else 0
    intercept = mean_y - slope * mean_x
    
    # Determine direction
    if slope > 0.01 * mean_y:
        direction = TrendDirection.DECLINING if metric_key in ["cost", "delay", "risk"] else TrendDirection.IMPROVING
    elif slope < -0.01 * mean_y:
        direction = TrendDirection.IMPROVING if metric_key in ["cost", "delay", "risk"] else TrendDirection.DECLINING
    else:
        direction = TrendDirection.STABLE
    
    # Forecast next value
    next_value = slope * n + intercept
    
    return {
        "direction": direction.value,
        "slope": round(slope, 4),
        "confidence": 0.7,
        "forecast_next": round(next_value, 2),
        "recent_average": round(mean_y, 2)
    }


__all__ = [
    "NUMPY_AVAILABLE",
    "RiskLevel",
    "TrendDirection",
    "ScheduleForecast",
    "CostForecast",
    "PerformanceMetrics",
    "calculate_performance_metrics",
    "predict_schedule_delay",
    "predict_cost_overrun",
    "analyze_trend"
]
