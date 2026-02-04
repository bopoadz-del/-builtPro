"""
Enterprise-ready consolidated takeoff wrapper.

This module delegates consolidated takeoff requests to the underlying
``backend.backend.services.consolidated_takeoff`` implementation.  It
extracts a project identifier and query from the incoming message and
returns a structured response.  Exceptions are caught and logged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .intent_router import router

try:
    from backend.backend.services import consolidated_takeoff as takeoff_service
except Exception:
    takeoff_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

from .rag_engine import _extract_project_id, _extract_query  # reuse helpers


def handle_consolidated_takeoff(message: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle consolidated takeoff requests."""
    context = context or {}
    project_id = _extract_project_id(message, context)
    query = _extract_query(message)
    try:
        if takeoff_service is None:
            raise RuntimeError("Consolidated takeoff implementation is unavailable")
        result = takeoff_service.run_consolidation(project_id, query)
    except Exception as exc:
        logger.exception("Consolidated takeoff error: %s", exc)
        result = "An error occurred while processing your request."
    return {"service": "consolidated_takeoff", "result": result}


# Register service on import
router.register(
    "consolidated_takeoff",
    [r"\bconsolidated\b"],
    handle_consolidated_takeoff,
)
