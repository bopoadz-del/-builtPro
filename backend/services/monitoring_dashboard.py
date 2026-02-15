"""
Monitoring Dashboard for BuilTPro Brain AI

Grafana-ready metrics, dashboards, and alerting.

Features:
- Real-time metrics collection
- Dashboard definitions
- Alert rules and thresholds
- Metric aggregation
- Prometheus-compatible export
- Custom dashboard builder
- SLA tracking
- Incident management

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
from threading import Lock

logger = logging.getLogger(__name__)


class MonitoringError(Exception):
    pass


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class MetricAggregation(str, Enum):
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    P95 = "p95"
    P99 = "p99"


@dataclass
class MetricPoint:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertRule:
    rule_id: str
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 60
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class Alert:
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    fired_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


@dataclass
class Dashboard:
    dashboard_id: str
    name: str
    panels: List[Dict[str, Any]] = field(default_factory=list)
    refresh_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLATarget:
    sla_id: str
    name: str
    target_percentage: float  # e.g., 99.9
    metric_name: str
    current_percentage: float = 100.0


class MonitoringDashboard:
    """Production-ready monitoring dashboard."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.dashboards: Dict[str, Dashboard] = {}
        self.sla_targets: Dict[str, SLATarget] = {}

        self.stats = {"metrics_recorded": 0, "alerts_fired": 0, "alerts_resolved": 0}

        self._create_default_dashboards()
        logger.info("Monitoring Dashboard initialized")

    def _create_default_dashboards(self):
        """Create default monitoring dashboards."""
        self.dashboards["system"] = Dashboard(
            dashboard_id="system", name="System Overview",
            panels=[
                {"title": "CPU Usage", "metric": "system.cpu", "type": "gauge"},
                {"title": "Memory Usage", "metric": "system.memory", "type": "gauge"},
                {"title": "Request Rate", "metric": "http.requests", "type": "graph"},
                {"title": "Error Rate", "metric": "http.errors", "type": "graph"},
                {"title": "Response Time", "metric": "http.latency", "type": "graph"},
            ]
        )
        self.dashboards["business"] = Dashboard(
            dashboard_id="business", name="Business Metrics",
            panels=[
                {"title": "Active Users", "metric": "users.active", "type": "stat"},
                {"title": "Projects", "metric": "projects.total", "type": "stat"},
                {"title": "API Calls", "metric": "api.calls", "type": "graph"},
            ]
        )

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric data point."""
        point = MetricPoint(name=name, value=value, labels=labels or {})
        self.metrics[name].append(point)
        self.stats["metrics_recorded"] += 1

        # Check alert rules
        self._evaluate_alerts(name, value)

    def _evaluate_alerts(self, metric_name: str, value: float):
        """Evaluate alert rules against a metric value."""
        for rule in self.alert_rules.values():
            if rule.metric_name != metric_name:
                continue

            triggered = False
            if rule.condition == "gt" and value > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and value < rule.threshold:
                triggered = True

            if triggered and rule.rule_id not in self.active_alerts:
                import secrets
                alert = Alert(
                    alert_id=f"alert_{secrets.token_hex(8)}",
                    rule_id=rule.rule_id, severity=rule.severity,
                    message=f"{rule.name}: {metric_name}={value} {rule.condition} {rule.threshold}"
                )
                self.active_alerts[rule.rule_id] = alert
                self.alert_history.append(alert)
                self.stats["alerts_fired"] += 1
                logger.warning(f"Alert fired: {alert.message}")

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.rule_id] = rule

    def acknowledge_alert(self, rule_id: str):
        """Acknowledge an active alert."""
        if rule_id in self.active_alerts:
            self.active_alerts[rule_id].status = AlertStatus.ACKNOWLEDGED

    def resolve_alert(self, rule_id: str):
        """Resolve an active alert."""
        if rule_id in self.active_alerts:
            alert = self.active_alerts.pop(rule_id)
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            self.stats["alerts_resolved"] += 1

    def get_metric_values(self, name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent metric values."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        points = [
            {"value": p.value, "timestamp": p.timestamp.isoformat()}
            for p in self.metrics.get(name, [])
            if p.timestamp > cutoff
        ]
        return points

    def aggregate_metric(self, name: str, aggregation: MetricAggregation, minutes: int = 60) -> float:
        """Aggregate metric values."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        values = [p.value for p in self.metrics.get(name, []) if p.timestamp > cutoff]

        if not values:
            return 0.0

        if aggregation == MetricAggregation.SUM:
            return sum(values)
        elif aggregation == MetricAggregation.AVG:
            return sum(values) / len(values)
        elif aggregation == MetricAggregation.MIN:
            return min(values)
        elif aggregation == MetricAggregation.MAX:
            return max(values)
        elif aggregation == MetricAggregation.COUNT:
            return float(len(values))
        elif aggregation == MetricAggregation.P95:
            sorted_vals = sorted(values)
            return sorted_vals[int(len(sorted_vals) * 0.95)]
        elif aggregation == MetricAggregation.P99:
            sorted_vals = sorted(values)
            return sorted_vals[int(len(sorted_vals) * 0.99)]
        return 0.0

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        for name, points in self.metrics.items():
            if points:
                latest = points[-1]
                clean_name = name.replace(".", "_")
                labels_str = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                if labels_str:
                    lines.append(f'{clean_name}{{{labels_str}}} {latest.value}')
                else:
                    lines.append(f'{clean_name} {latest.value}')
        return "\n".join(lines)

    def set_sla_target(self, sla: SLATarget):
        """Set an SLA target."""
        self.sla_targets[sla.sla_id] = sla

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats, "active_alerts": len(self.active_alerts),
                "dashboards": len(self.dashboards), "metrics_tracked": len(self.metrics),
                "sla_targets": len(self.sla_targets)}


monitoring_dashboard = MonitoringDashboard()
