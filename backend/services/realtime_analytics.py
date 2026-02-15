"""
Real-time Analytics Engine for BuilTPro Brain AI

Provides live project metrics, KPI tracking, WebSocket streaming,
dashboard aggregations, and performance scoring.

Features:
- Real-time metric computation
- WebSocket streaming for live updates
- KPI dashboards with aggregations
- Trend analysis and forecasting
- Performance scoring algorithms
- Time-series data processing

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
import statistics
import asyncio
from threading import Lock

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class AnalyticsError(Exception):
    """Base exception for analytics engine errors."""
    pass


class MetricNotFoundError(AnalyticsError):
    """Raised when a requested metric does not exist."""
    pass


class StreamError(AnalyticsError):
    """Raised when WebSocket streaming fails."""
    pass


class AggregationError(AnalyticsError):
    """Raised when metric aggregation fails."""
    pass


# ============================================================================
# Enums
# ============================================================================


class MetricType(str, Enum):
    """Types of metrics tracked by the analytics engine."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"
    PERCENTAGE = "percentage"


class AggregationMethod(str, Enum):
    """Methods for aggregating time-series data."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    P50 = "p50"
    P95 = "p95"
    P99 = "p99"


class TrendDirection(str, Enum):
    """Direction of metric trends."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class PerformanceStatus(str, Enum):
    """Performance status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricDefinition:
    """Definition of a tracked metric."""
    name: str
    type: MetricType
    description: str
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KPI:
    """Key Performance Indicator definition."""
    name: str
    metric_name: str
    target: float
    current: float
    unit: str
    trend: TrendDirection
    status: PerformanceStatus
    change_percentage: float
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardMetrics:
    """Aggregated metrics for dashboard display."""
    project_id: str
    kpis: List[KPI]
    total_cost: float
    budget_utilization: float
    schedule_performance: float
    safety_score: float
    quality_score: float
    team_productivity: float
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrendAnalysis:
    """Trend analysis results for a metric."""
    metric_name: str
    direction: TrendDirection
    change_rate: float
    volatility: float
    forecast_next: Optional[float]
    confidence: float
    data_points: int
    period_days: int


@dataclass
class StreamSubscription:
    """WebSocket stream subscription."""
    subscription_id: str
    metric_names: List[str]
    filters: Dict[str, Any]
    callback: Callable
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_update: Optional[datetime] = None


# ============================================================================
# Real-time Analytics Engine
# ============================================================================


class RealtimeAnalyticsEngine:
    """
    Production-ready real-time analytics engine.

    Provides comprehensive analytics capabilities including:
    - Real-time metric tracking
    - WebSocket streaming
    - KPI dashboards
    - Trend analysis
    - Performance scoring
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global analytics engine."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the analytics engine."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Storage
        self.metrics: Dict[str, MetricDefinition] = {}
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.subscriptions: Dict[str, StreamSubscription] = {}

        # Configuration
        self.retention_hours = 72  # Keep 72 hours of data
        self.aggregation_interval_seconds = 60

        logger.info("Real-time Analytics Engine initialized")

    # ========================================================================
    # Metric Registration & Tracking
    # ========================================================================

    def register_metric(
        self,
        name: str,
        type: MetricType,
        description: str,
        unit: str,
        tags: Optional[Dict[str, str]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> MetricDefinition:
        """
        Register a new metric for tracking.

        Args:
            name: Unique metric identifier
            type: Type of metric (counter, gauge, etc.)
            description: Human-readable description
            unit: Unit of measurement
            tags: Optional tags for categorization
            thresholds: Optional threshold values (warning, critical, etc.)

        Returns:
            MetricDefinition object
        """
        try:
            metric_def = MetricDefinition(
                name=name,
                type=type,
                description=description,
                unit=unit,
                tags=tags or {},
                thresholds=thresholds or {}
            )

            self.metrics[name] = metric_def
            logger.info(f"Registered metric: {name} ({type})")

            return metric_def

        except Exception as e:
            logger.error(f"Failed to register metric {name}: {e}")
            raise AnalyticsError(f"Metric registration failed: {e}")

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a new metric value.

        Args:
            name: Metric name (must be registered)
            value: Metric value
            tags: Optional tags for this data point
            metadata: Optional metadata
        """
        try:
            if name not in self.metrics:
                raise MetricNotFoundError(f"Metric not registered: {name}")

            metric_value = MetricValue(
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metadata=metadata or {}
            )

            self.metric_data[name].append(metric_value)

            # Trigger real-time updates
            self._notify_subscribers(name, metric_value)

        except MetricNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
            raise AnalyticsError(f"Metric recording failed: {e}")

    # ========================================================================
    # WebSocket Streaming
    # ========================================================================

    def subscribe(
        self,
        subscription_id: str,
        metric_names: List[str],
        callback: Callable,
        filters: Optional[Dict[str, Any]] = None
    ) -> StreamSubscription:
        """
        Subscribe to real-time metric updates via WebSocket.

        Args:
            subscription_id: Unique subscription identifier
            metric_names: List of metrics to stream
            callback: Async callback function for updates
            filters: Optional filters for data points

        Returns:
            StreamSubscription object
        """
        try:
            # Validate metrics
            for metric_name in metric_names:
                if metric_name not in self.metrics:
                    raise MetricNotFoundError(f"Metric not found: {metric_name}")

            subscription = StreamSubscription(
                subscription_id=subscription_id,
                metric_names=metric_names,
                filters=filters or {},
                callback=callback
            )

            self.subscriptions[subscription_id] = subscription
            logger.info(f"Created subscription {subscription_id} for {len(metric_names)} metrics")

            return subscription

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise StreamError(f"Subscription failed: {e}")

    def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed subscription {subscription_id}")

    def _notify_subscribers(self, metric_name: str, value: MetricValue) -> None:
        """Notify all subscribers of a new metric value."""
        for sub in self.subscriptions.values():
            if metric_name in sub.metric_names:
                try:
                    # Apply filters if any
                    if self._matches_filters(value, sub.filters):
                        sub.callback(metric_name, value)
                        sub.last_update = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")

    def _matches_filters(self, value: MetricValue, filters: Dict[str, Any]) -> bool:
        """Check if a metric value matches subscription filters."""
        if not filters:
            return True

        # Tag filters
        if 'tags' in filters:
            for key, expected in filters['tags'].items():
                if value.tags.get(key) != expected:
                    return False

        # Value range filters
        if 'min_value' in filters and value.value < filters['min_value']:
            return False
        if 'max_value' in filters and value.value > filters['max_value']:
            return False

        return True

    # ========================================================================
    # Aggregations & KPIs
    # ========================================================================

    def aggregate(
        self,
        metric_name: str,
        method: AggregationMethod,
        period_hours: int = 24,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """
        Aggregate metric data over a time period.

        Args:
            metric_name: Metric to aggregate
            method: Aggregation method (sum, average, etc.)
            period_hours: Time period in hours
            tags: Optional tag filters

        Returns:
            Aggregated value or None if no data
        """
        try:
            if metric_name not in self.metric_data:
                return None

            cutoff = datetime.utcnow() - timedelta(hours=period_hours)

            # Filter data points
            values = [
                mv.value for mv in self.metric_data[metric_name]
                if mv.timestamp >= cutoff and (
                    not tags or all(mv.tags.get(k) == v for k, v in tags.items())
                )
            ]

            if not values:
                return None

            # Apply aggregation
            if method == AggregationMethod.SUM:
                return sum(values)
            elif method == AggregationMethod.AVERAGE:
                return statistics.mean(values)
            elif method == AggregationMethod.MIN:
                return min(values)
            elif method == AggregationMethod.MAX:
                return max(values)
            elif method == AggregationMethod.COUNT:
                return float(len(values))
            elif method == AggregationMethod.P50:
                return statistics.median(values)
            elif method == AggregationMethod.P95:
                return statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values)
            elif method == AggregationMethod.P99:
                return statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)

        except Exception as e:
            logger.error(f"Aggregation failed for {metric_name}: {e}")
            raise AggregationError(f"Failed to aggregate: {e}")

    def calculate_kpi(
        self,
        name: str,
        metric_name: str,
        target: float,
        unit: str,
        period_hours: int = 24
    ) -> KPI:
        """
        Calculate a KPI based on metric data.

        Args:
            name: KPI name
            metric_name: Source metric
            target: Target value for the KPI
            unit: Unit of measurement
            period_hours: Time period for calculation

        Returns:
            KPI object with current status and trend
        """
        try:
            # Get current value
            current = self.aggregate(metric_name, AggregationMethod.AVERAGE, period_hours)
            if current is None:
                current = 0.0

            # Get previous period value for trend
            previous = self.aggregate(
                metric_name,
                AggregationMethod.AVERAGE,
                period_hours * 2
            )
            if previous is None:
                previous = current

            # Calculate change
            change_percentage = ((current - previous) / previous * 100) if previous != 0 else 0.0

            # Determine trend
            trend = self._determine_trend(current, previous, change_percentage)

            # Determine status
            status = self._determine_status(current, target)

            return KPI(
                name=name,
                metric_name=metric_name,
                target=target,
                current=current,
                unit=unit,
                trend=trend,
                status=status,
                change_percentage=change_percentage,
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Failed to calculate KPI {name}: {e}")
            raise AnalyticsError(f"KPI calculation failed: {e}")

    def generate_dashboard(self, project_id: str) -> DashboardMetrics:
        """
        Generate comprehensive dashboard metrics for a project.

        Args:
            project_id: Project identifier

        Returns:
            DashboardMetrics with all key performance indicators
        """
        try:
            # Calculate key KPIs
            kpis = [
                self.calculate_kpi("Budget Health", "budget_utilization", 100.0, "%"),
                self.calculate_kpi("Schedule Performance", "schedule_performance_index", 1.0, "index"),
                self.calculate_kpi("Safety Score", "safety_score", 100.0, "points"),
                self.calculate_kpi("Quality Score", "quality_score", 100.0, "points"),
                self.calculate_kpi("Team Productivity", "team_productivity", 100.0, "%"),
            ]

            # Aggregate high-level metrics
            total_cost = self.aggregate("total_project_cost", AggregationMethod.SUM, 24) or 0.0
            budget_util = self.aggregate("budget_utilization", AggregationMethod.AVERAGE, 24) or 0.0
            schedule_perf = self.aggregate("schedule_performance_index", AggregationMethod.AVERAGE, 24) or 1.0
            safety = self.aggregate("safety_score", AggregationMethod.AVERAGE, 24) or 100.0
            quality = self.aggregate("quality_score", AggregationMethod.AVERAGE, 24) or 100.0
            productivity = self.aggregate("team_productivity", AggregationMethod.AVERAGE, 24) or 100.0

            return DashboardMetrics(
                project_id=project_id,
                kpis=kpis,
                total_cost=total_cost,
                budget_utilization=budget_util,
                schedule_performance=schedule_perf,
                safety_score=safety,
                quality_score=quality,
                team_productivity=productivity
            )

        except Exception as e:
            logger.error(f"Failed to generate dashboard for {project_id}: {e}")
            raise AnalyticsError(f"Dashboard generation failed: {e}")

    # ========================================================================
    # Trend Analysis
    # ========================================================================

    def analyze_trend(
        self,
        metric_name: str,
        period_days: int = 7,
        forecast: bool = True
    ) -> TrendAnalysis:
        """
        Analyze metric trends and optionally forecast next value.

        Args:
            metric_name: Metric to analyze
            period_days: Analysis period in days
            forecast: Whether to forecast next value

        Returns:
            TrendAnalysis with direction, rate, and optional forecast
        """
        try:
            if metric_name not in self.metric_data:
                raise MetricNotFoundError(f"Metric not found: {metric_name}")

            cutoff = datetime.utcnow() - timedelta(days=period_days)
            values = [
                mv.value for mv in self.metric_data[metric_name]
                if mv.timestamp >= cutoff
            ]

            if len(values) < 2:
                # Not enough data
                return TrendAnalysis(
                    metric_name=metric_name,
                    direction=TrendDirection.STABLE,
                    change_rate=0.0,
                    volatility=0.0,
                    forecast_next=None,
                    confidence=0.0,
                    data_points=len(values),
                    period_days=period_days
                )

            # Calculate trend direction
            direction = self._calculate_trend_direction(values)

            # Calculate change rate
            change_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0.0

            # Calculate volatility (coefficient of variation)
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0.0
            volatility = (stdev / mean * 100) if mean != 0 else 0.0

            # Simple forecast (linear extrapolation)
            forecast_next = None
            confidence = 0.0
            if forecast and len(values) >= 3:
                forecast_next = values[-1] + (values[-1] - values[0]) / len(values)
                confidence = max(0, min(100, 100 - volatility))

            return TrendAnalysis(
                metric_name=metric_name,
                direction=direction,
                change_rate=change_rate,
                volatility=volatility,
                forecast_next=forecast_next,
                confidence=confidence,
                data_points=len(values),
                period_days=period_days
            )

        except MetricNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Trend analysis failed for {metric_name}: {e}")
            raise AnalyticsError(f"Trend analysis failed: {e}")

    # ========================================================================
    # Helpers
    # ========================================================================

    def _determine_trend(self, current: float, previous: float, change_pct: float) -> TrendDirection:
        """Determine trend direction based on values."""
        if abs(change_pct) < 2.0:
            return TrendDirection.STABLE
        elif abs(change_pct) > 20.0:
            return TrendDirection.VOLATILE
        elif current > previous:
            return TrendDirection.UP
        else:
            return TrendDirection.DOWN

    def _determine_status(self, current: float, target: float) -> PerformanceStatus:
        """Determine performance status based on target."""
        ratio = (current / target * 100) if target != 0 else 100.0

        if ratio >= 95:
            return PerformanceStatus.EXCELLENT
        elif ratio >= 85:
            return PerformanceStatus.GOOD
        elif ratio >= 70:
            return PerformanceStatus.FAIR
        elif ratio >= 50:
            return PerformanceStatus.POOR
        else:
            return PerformanceStatus.CRITICAL

    def _calculate_trend_direction(self, values: List[float]) -> TrendDirection:
        """Calculate overall trend direction from time series."""
        if len(values) < 2:
            return TrendDirection.STABLE

        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        y = values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return TrendDirection.STABLE

        slope = numerator / denominator

        # Calculate volatility
        stdev = statistics.stdev(values)
        mean = statistics.mean(values)
        cv = (stdev / mean * 100) if mean != 0 else 0

        if cv > 30:
            return TrendDirection.VOLATILE
        elif abs(slope) < 0.01:
            return TrendDirection.STABLE
        elif slope > 0:
            return TrendDirection.UP
        else:
            return TrendDirection.DOWN

    def cleanup_old_data(self) -> int:
        """Remove data older than retention period. Returns number of points removed."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        removed = 0

        for metric_name, data in self.metric_data.items():
            original_len = len(data)
            # Keep only recent data
            while data and data[0].timestamp < cutoff:
                data.popleft()
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old metric data points")

        return removed


# ============================================================================
# Singleton Instance
# ============================================================================

# Global singleton instance
analytics_engine = RealtimeAnalyticsEngine()
