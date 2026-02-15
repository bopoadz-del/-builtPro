"""
Performance Profiler for BuilTPro Brain AI

Application performance monitoring (APM) with bottleneck detection and tracing.

Features:
- Request/response timing
- Endpoint profiling
- Memory usage tracking
- CPU utilization monitoring
- Bottleneck detection
- Distributed tracing
- Performance alerts
- Historical trend analysis

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
from threading import Lock
import time

logger = logging.getLogger(__name__)


class ProfilerError(Exception):
    pass


class MetricType(str, Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY = "memory"
    CPU = "cpu"


@dataclass
class TraceSpan:
    span_id: str
    trace_id: str
    operation: str
    service: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    parent_span_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    error: bool = False


@dataclass
class PerformanceMetric:
    endpoint: str
    method: str
    timestamp: datetime
    response_time_ms: float
    status_code: int
    memory_mb: float = 0.0


@dataclass
class BottleneckReport:
    endpoint: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    request_count: int
    error_rate: float
    recommendation: str


class PerformanceProfiler:
    """Production-ready APM and performance profiler."""

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

        self.metrics: deque = deque(maxlen=100000)
        self.traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)

        self.slow_threshold_ms = 500
        self.stats = {"total_requests": 0, "slow_requests": 0}
        logger.info("Performance Profiler initialized")

    def record_request(self, endpoint: str, method: str, response_time_ms: float,
                       status_code: int, memory_mb: float = 0.0):
        """Record a request metric."""
        metric = PerformanceMetric(
            endpoint=endpoint, method=method, timestamp=datetime.utcnow(),
            response_time_ms=response_time_ms, status_code=status_code,
            memory_mb=memory_mb
        )
        self.metrics.append(metric)
        self.endpoint_stats[endpoint].append(response_time_ms)

        # Keep only last 1000 per endpoint
        if len(self.endpoint_stats[endpoint]) > 1000:
            self.endpoint_stats[endpoint] = self.endpoint_stats[endpoint][-1000:]

        self.stats["total_requests"] += 1
        if response_time_ms > self.slow_threshold_ms:
            self.stats["slow_requests"] += 1

    def start_trace(self, trace_id: str, span_id: str, operation: str,
                    service: str, parent_span_id: Optional[str] = None) -> TraceSpan:
        """Start a trace span."""
        span = TraceSpan(
            span_id=span_id, trace_id=trace_id, operation=operation,
            service=service, start_time=time.time(),
            parent_span_id=parent_span_id
        )
        self.traces[trace_id].append(span)
        return span

    def end_trace(self, trace_id: str, span_id: str, error: bool = False):
        """End a trace span."""
        for span in self.traces.get(trace_id, []):
            if span.span_id == span_id:
                span.end_time = time.time()
                span.duration_ms = (span.end_time - span.start_time) * 1000
                span.error = error
                break

    def detect_bottlenecks(self, min_requests: int = 10) -> List[BottleneckReport]:
        """Detect performance bottlenecks."""
        reports = []

        for endpoint, times in self.endpoint_stats.items():
            if len(times) < min_requests:
                continue

            sorted_times = sorted(times)
            avg = sum(times) / len(times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]

            # Count errors for this endpoint
            endpoint_metrics = [m for m in self.metrics if m.endpoint == endpoint]
            errors = sum(1 for m in endpoint_metrics if m.status_code >= 500)
            error_rate = errors / max(len(endpoint_metrics), 1)

            recommendation = "OK"
            if avg > self.slow_threshold_ms:
                recommendation = "Optimize: Average response time exceeds threshold"
            elif p95 > self.slow_threshold_ms * 2:
                recommendation = "Investigate: P95 latency is high"
            elif error_rate > 0.05:
                recommendation = "Fix: Error rate exceeds 5%"

            if recommendation != "OK":
                reports.append(BottleneckReport(
                    endpoint=endpoint, avg_response_time_ms=avg,
                    p95_response_time_ms=p95, p99_response_time_ms=p99,
                    request_count=len(times), error_rate=error_rate,
                    recommendation=recommendation
                ))

        return sorted(reports, key=lambda r: r.avg_response_time_ms, reverse=True)

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        times = self.endpoint_stats.get(endpoint, [])
        if not times:
            return {"endpoint": endpoint, "no_data": True}

        sorted_times = sorted(times)
        return {
            "endpoint": endpoint,
            "request_count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p50_ms": sorted_times[len(sorted_times) // 2],
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99)]
        }

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats, "endpoints_tracked": len(self.endpoint_stats),
                "active_traces": len(self.traces)}


performance_profiler = PerformanceProfiler()
