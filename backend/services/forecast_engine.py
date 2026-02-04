"""Forecast engine utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


@dataclass
class ScheduleForecast:
    delay_days: int
    probability_on_time: float
    risk_level: RiskLevel


@dataclass
class CostForecast:
    forecasted_cost: float
    original_budget: float
    variance: float
    variance_percent: float
    probability_within_budget: float


@dataclass
class PerformanceMetrics:
    earned_value: float
    schedule_performance_index: float
    cost_performance_index: float


def predict_schedule_delay(schedule_data: Dict[str, float | int | str]) -> ScheduleForecast:
    current_progress = float(schedule_data.get("current_progress", 0))
    planned_progress = float(schedule_data.get("planned_progress", 0))
    variance = current_progress - planned_progress
    delay_days = max(int(-variance), 0)
    if variance >= 0:
        probability = 0.8
        risk = RiskLevel.LOW
    elif variance >= -10:
        probability = 0.6
        risk = RiskLevel.MEDIUM
    else:
        probability = 0.4
        risk = RiskLevel.HIGH
    return ScheduleForecast(delay_days=delay_days, probability_on_time=probability, risk_level=risk)


def predict_cost_overrun(cost_data: Dict[str, float | int]) -> CostForecast:
    budget = float(cost_data.get("budget", 0))
    actual_cost = float(cost_data.get("actual_cost", 0))
    percent_complete = float(cost_data.get("percent_complete", 0))
    forecasted_cost = actual_cost / max(percent_complete / 100, 0.01)
    variance = forecasted_cost - budget
    variance_percent = (variance / budget * 100) if budget else 0
    probability = 0.7 if variance <= 0 else 0.4
    return CostForecast(
        forecasted_cost=forecasted_cost,
        original_budget=budget,
        variance=variance,
        variance_percent=variance_percent,
        probability_within_budget=probability,
    )


def calculate_performance_metrics(
    budget_at_completion: float,
    actual_cost: float,
    percent_complete: float,
    planned_percent: float,
) -> PerformanceMetrics:
    earned_value = budget_at_completion * (percent_complete / 100)
    planned_value = budget_at_completion * (planned_percent / 100)
    schedule_performance_index = earned_value / planned_value if planned_value else 1.0
    cost_performance_index = earned_value / actual_cost if actual_cost else 1.0
    return PerformanceMetrics(
        earned_value=earned_value,
        schedule_performance_index=schedule_performance_index,
        cost_performance_index=cost_performance_index,
    )


def analyze_trend(data_points: List[Dict[str, float | str]], value_key: str) -> Dict[str, object]:
    values = [float(item[value_key]) for item in data_points if value_key in item]
    if len(values) < 2:
        return {"direction": TrendDirection.STABLE.value, "forecast_next": None}
    delta = values[-1] - values[0]
    if delta < 0:
        direction = TrendDirection.IMPROVING
    elif delta > 0:
        direction = TrendDirection.DECLINING
    else:
        direction = TrendDirection.STABLE
    forecast_next = values[-1] + (delta / max(len(values) - 1, 1))
    return {"direction": direction.value, "forecast_next": forecast_next}
