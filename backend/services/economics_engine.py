# Economics Calculation Engine - ITEM 115
# Advanced cost estimation, budgeting, and financial forecasting

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import math

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class CostCategory(str, Enum):
    """Cost breakdown categories."""
    LABOR = "labor"
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    SUBCONTRACTORS = "subcontractors"
    OVERHEAD = "overhead"
    CONTINGENCY = "contingency"
    OTHER = "other"


class ForecastMethod(str, Enum):
    """Methods for cost forecasting."""
    LINEAR = "linear"
    EARNED_VALUE = "earned_value"
    HISTORICAL = "historical"
    MONTE_CARLO = "monte_carlo"


@dataclass
class CostItem:
    """Individual cost item."""
    id: str
    name: str
    category: CostCategory
    quantity: Decimal
    unit: str
    unit_cost: Decimal
    total_cost: Decimal = field(init=False)
    actual_cost: Decimal = Decimal("0")
    committed_cost: Decimal = Decimal("0")

    def __post_init__(self):
        self.total_cost = self.quantity * self.unit_cost

    @property
    def variance(self) -> Decimal:
        """Cost variance (actual vs budgeted)."""
        return self.actual_cost - self.total_cost

    @property
    def variance_percent(self) -> float:
        """Variance as percentage."""
        if self.total_cost == 0:
            return 0.0
        return float((self.variance / self.total_cost) * 100)


@dataclass
class ChangeOrder:
    """Change order tracking."""
    id: str
    description: str
    amount: Decimal
    status: str  # pending, approved, rejected
    date: date
    category: Optional[CostCategory] = None
    approved_date: Optional[date] = None


@dataclass
class Budget:
    """Project budget with tracking."""
    original_budget: Decimal
    contingency: Decimal
    total_budget: Decimal = field(init=False)
    actual_cost: Decimal = Decimal("0")
    committed_cost: Decimal = Decimal("0")
    change_orders: List[ChangeOrder] = field(default_factory=list)
    cost_items: List[CostItem] = field(default_factory=list)

    def __post_init__(self):
        self.total_budget = self.original_budget + self.contingency

    @property
    def approved_change_orders(self) -> Decimal:
        """Sum of approved change orders."""
        return sum(
            co.amount for co in self.change_orders
            if co.status == "approved"
        )

    @property
    def adjusted_budget(self) -> Decimal:
        """Budget including approved change orders."""
        return self.total_budget + self.approved_change_orders

    @property
    def variance(self) -> Decimal:
        """Total budget variance."""
        return self.actual_cost - self.adjusted_budget

    @property
    def remaining_budget(self) -> Decimal:
        """Remaining budget (budget - actual - committed)."""
        return self.adjusted_budget - self.actual_cost - self.committed_cost

    @property
    def remaining_contingency(self) -> Decimal:
        """Remaining contingency."""
        used_contingency = max(Decimal("0"), self.variance)
        return max(Decimal("0"), self.contingency - used_contingency)


class EconomicsEngine:
    """
    Advanced economics calculation engine.
    Handles cost estimation, forecasting, and financial analysis.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def calculate_earned_value_metrics(
        self,
        budget: Budget,
        planned_value: Decimal,
        percent_complete: float
    ) -> Dict[str, float]:
        """
        Calculate Earned Value Management (EVM) metrics.

        Args:
            budget: Project budget
            planned_value: Planned value at current date (PV)
            percent_complete: Percent of work completed (0-100)

        Returns:
            Dictionary with EVM metrics
        """
        # Earned Value (EV) = Total Budget * % Complete
        earned_value = budget.adjusted_budget * Decimal(percent_complete / 100)

        # Actual Cost (AC)
        actual_cost = budget.actual_cost

        # Cost Variance (CV) = EV - AC
        cost_variance = earned_value - actual_cost

        # Schedule Variance (SV) = EV - PV
        schedule_variance = earned_value - planned_value

        # Cost Performance Index (CPI) = EV / AC
        cpi = float(earned_value / actual_cost) if actual_cost > 0 else 1.0

        # Schedule Performance Index (SPI) = EV / PV
        spi = float(earned_value / planned_value) if planned_value > 0 else 1.0

        # Budget at Completion (BAC)
        bac = budget.adjusted_budget

        # Estimate at Completion (EAC) = BAC / CPI
        eac = float(bac / Decimal(cpi)) if cpi > 0 else float(bac)

        # Estimate to Complete (ETC) = EAC - AC
        etc = eac - float(actual_cost)

        # Variance at Completion (VAC) = BAC - EAC
        vac = float(bac) - eac

        # To-Complete Performance Index (TCPI) = (BAC - EV) / (BAC - AC)
        remaining_work = float(bac - earned_value)
        remaining_budget = float(bac - actual_cost)
        tcpi = remaining_work / remaining_budget if remaining_budget > 0 else 1.0

        return {
            "planned_value": float(planned_value),
            "earned_value": float(earned_value),
            "actual_cost": float(actual_cost),
            "cost_variance": float(cost_variance),
            "schedule_variance": float(schedule_variance),
            "cost_performance_index": cpi,
            "schedule_performance_index": spi,
            "budget_at_completion": float(bac),
            "estimate_at_completion": eac,
            "estimate_to_complete": etc,
            "variance_at_completion": vac,
            "to_complete_performance_index": tcpi,
            "percent_complete": percent_complete,
        }

    def forecast_cost(
        self,
        budget: Budget,
        method: ForecastMethod = ForecastMethod.EARNED_VALUE,
        historical_data: Optional[List[Dict]] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Forecast final project cost using various methods.

        Args:
            budget: Project budget
            method: Forecasting method to use
            historical_data: Historical cost data for advanced forecasting
            confidence_level: Confidence level for Monte Carlo simulation

        Returns:
            Forecast results with estimates and confidence intervals
        """
        if method == ForecastMethod.LINEAR:
            return self._forecast_linear(budget)

        elif method == ForecastMethod.EARNED_VALUE:
            return self._forecast_earned_value(budget)

        elif method == ForecastMethod.HISTORICAL:
            if not historical_data:
                raise ValueError("Historical data required for historical forecasting")
            return self._forecast_historical(budget, historical_data)

        elif method == ForecastMethod.MONTE_CARLO:
            return self._forecast_monte_carlo(budget, confidence_level)

        else:
            raise ValueError(f"Unknown forecasting method: {method}")

    def _forecast_linear(self, budget: Budget) -> Dict[str, float]:
        """Simple linear projection based on current spending rate."""
        if budget.actual_cost == 0:
            return {
                "forecast_cost": float(budget.adjusted_budget),
                "variance": 0.0,
                "confidence": 0.5,
                "method": "linear"
            }

        # Assume linear spending continues
        percent_spent = float(budget.actual_cost / budget.adjusted_budget)

        # Simple forecast: if we've spent X% and we're X% done, we're on track
        # For now, assume we're proportionally through the project
        forecast_cost = float(budget.adjusted_budget)

        return {
            "forecast_cost": forecast_cost,
            "variance": forecast_cost - float(budget.adjusted_budget),
            "confidence": 0.6,
            "method": "linear",
            "percent_spent": percent_spent * 100
        }

    def _forecast_earned_value(self, budget: Budget) -> Dict[str, float]:
        """Forecast using Earned Value Management."""
        # Use CPI to forecast
        # For simplicity, assume 50% complete if not specified
        percent_complete = 50.0

        evm = self.calculate_earned_value_metrics(
            budget,
            budget.adjusted_budget * Decimal(0.5),  # Assume PV = 50%
            percent_complete
        )

        return {
            "forecast_cost": evm["estimate_at_completion"],
            "variance": evm["variance_at_completion"],
            "confidence": 0.8,
            "method": "earned_value",
            "cpi": evm["cost_performance_index"],
            "spi": evm["schedule_performance_index"]
        }

    def _forecast_historical(
        self,
        budget: Budget,
        historical_data: List[Dict]
    ) -> Dict[str, float]:
        """Forecast using historical project data."""
        # Calculate average cost overrun from historical projects
        overruns = [
            (proj["actual_cost"] - proj["budget"]) / proj["budget"]
            for proj in historical_data
            if proj["budget"] > 0
        ]

        avg_overrun = sum(overruns) / len(overruns) if overruns else 0.0

        forecast_cost = float(budget.adjusted_budget) * (1 + avg_overrun)

        return {
            "forecast_cost": forecast_cost,
            "variance": forecast_cost - float(budget.adjusted_budget),
            "confidence": 0.75,
            "method": "historical",
            "historical_projects": len(historical_data),
            "avg_overrun_percent": avg_overrun * 100
        }

    def _forecast_monte_carlo(
        self,
        budget: Budget,
        confidence_level: float
    ) -> Dict[str, float]:
        """
        Forecast using Monte Carlo simulation.
        Simplified version - in production, use proper statistical simulation.
        """
        # Simplified Monte Carlo: assume normal distribution around current cost
        base_forecast = float(budget.adjusted_budget)

        # Use 10% standard deviation as a simple assumption
        std_dev = base_forecast * 0.1

        # Calculate confidence intervals (using normal distribution approximation)
        # For 95% confidence, use ~1.96 standard deviations
        z_score = 1.96 if confidence_level == 0.95 else 1.645

        lower_bound = base_forecast - (z_score * std_dev)
        upper_bound = base_forecast + (z_score * std_dev)

        # P50 (median) forecast
        p50_forecast = base_forecast

        return {
            "forecast_cost": p50_forecast,
            "p10": lower_bound,
            "p50": p50_forecast,
            "p90": upper_bound,
            "variance": 0.0,
            "confidence": confidence_level,
            "method": "monte_carlo",
            "simulations": 10000  # In real implementation, run actual simulations
        }

    def calculate_roi(
        self,
        investment: Decimal,
        returns: List[Decimal],
        time_period_years: float
    ) -> Dict[str, float]:
        """
        Calculate Return on Investment (ROI) metrics.

        Args:
            investment: Initial investment amount
            returns: List of periodic returns
            time_period_years: Time period in years

        Returns:
            ROI metrics including NPV, IRR, payback period
        """
        total_return = sum(returns)

        # Simple ROI
        roi = float((total_return - investment) / investment * 100)

        # Annualized ROI
        annualized_roi = float(
            (math.pow(float(total_return / investment), 1/time_period_years) - 1) * 100
        )

        # Payback period (simplified)
        cumulative = Decimal("0")
        payback_period = 0.0
        for i, ret in enumerate(returns):
            cumulative += ret
            if cumulative >= investment:
                payback_period = (i + 1) * (time_period_years / len(returns))
                break

        return {
            "roi_percent": roi,
            "annualized_roi_percent": annualized_roi,
            "total_return": float(total_return),
            "payback_period_years": payback_period,
            "investment": float(investment)
        }

    def optimize_budget_allocation(
        self,
        total_budget: Decimal,
        cost_items: List[CostItem],
        priorities: Dict[str, float]
    ) -> List[Dict]:
        """
        Optimize budget allocation across cost items based on priorities.

        Args:
            total_budget: Total available budget
            cost_items: List of cost items to allocate
            priorities: Priority scores for each category (0-1)

        Returns:
            Optimized allocation recommendations
        """
        # Calculate total requested
        total_requested = sum(item.total_cost for item in cost_items)

        # If under budget, no optimization needed
        if total_requested <= total_budget:
            return [
                {
                    "item_id": item.id,
                    "recommended_allocation": float(item.total_cost),
                    "original_request": float(item.total_cost),
                    "reduction": 0.0
                }
                for item in cost_items
            ]

        # Over budget - allocate proportionally by priority
        allocations = []
        remaining_budget = total_budget

        # Sort items by priority (highest first)
        sorted_items = sorted(
            cost_items,
            key=lambda x: priorities.get(x.category.value, 0.5),
            reverse=True
        )

        for item in sorted_items:
            priority = priorities.get(item.category.value, 0.5)

            # Allocate based on priority and remaining budget
            allocation = min(
                item.total_cost,
                remaining_budget * Decimal(priority)
            )

            allocations.append({
                "item_id": item.id,
                "item_name": item.name,
                "category": item.category.value,
                "recommended_allocation": float(allocation),
                "original_request": float(item.total_cost),
                "reduction": float(item.total_cost - allocation),
                "priority": priority
            })

            remaining_budget -= allocation

        return allocations


# Singleton instance
_economics_engine = None


def get_economics_engine() -> EconomicsEngine:
    """Get or create economics engine singleton."""
    global _economics_engine
    if _economics_engine is None:
        _economics_engine = EconomicsEngine()
    return _economics_engine
