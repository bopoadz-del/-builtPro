"""Stub analytics service implementation."""

from __future__ import annotations


def query_logs(project_id: str | None, query: str) -> str:
    project_label = project_id or "unknown"
    return f"Stub analytics for {project_label}: {query}"
