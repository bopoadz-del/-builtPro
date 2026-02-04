"""Anomaly detection helpers."""

from __future__ import annotations

from typing import Any, Dict, List


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def detect_anomalies(data_stream: List[Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for entry in data_stream:
        if not isinstance(entry, dict):
            continue
        if "risk_score" in entry:
            score = float(entry.get("risk_score", 0))
            if score >= 0.9:
                severity = "critical"
            elif score >= 0.8:
                severity = "high"
            elif score >= 0.7:
                severity = "medium"
            else:
                severity = "low"
            if score >= 0.7:
                findings.append({"type": "risk", "severity": severity, "score": score})
        if "progress_percent" in entry and "expected_progress_percent" in entry:
            progress = float(entry.get("progress_percent", 0))
            expected = float(entry.get("expected_progress_percent", 0))
            if progress + 5 < expected:
                findings.append({"type": "schedule", "severity": "high", "variance": expected - progress})
        if "planned_cost" in entry and "actual_cost" in entry:
            planned = float(entry.get("planned_cost", 0))
            actual = float(entry.get("actual_cost", 0))
            if actual > planned:
                findings.append({"type": "cost", "severity": "medium", "variance": actual - planned})
        if entry.get("incidents", 0):
            findings.append({"type": "safety", "severity": "medium", "incidents": entry.get("incidents")})
        if entry.get("defects", 0):
            findings.append({"type": "quality", "severity": "medium", "defects": entry.get("defects")})

    findings.sort(key=lambda item: _SEVERITY_ORDER.get(item.get("severity", "low"), 3))
    return findings
