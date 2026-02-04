"""Stub consolidated takeoff implementation."""

from __future__ import annotations


def run_consolidation(project_id: str | None, query: str) -> str:
    project_label = project_id or "unknown"
    return f"Stub consolidated takeoff for {project_label}: {query}"
