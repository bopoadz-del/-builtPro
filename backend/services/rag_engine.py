"""Helper utilities for extracting project metadata and queries."""

from __future__ import annotations

from typing import Any, Dict, Optional


def _extract_project_id(message: Any, context: Optional[Dict[str, Any]] = None) -> str:
    context = context or {}
    if "project_id" in context:
        return str(context["project_id"])
    if isinstance(message, dict) and "project_id" in message:
        return str(message["project_id"])
    return "unknown"


def _extract_query(message: Any) -> str:
    if isinstance(message, dict):
        for key in ("content", "text", "query"):
            if key in message and message[key] is not None:
                return str(message[key])
        return ""
    return str(message)
