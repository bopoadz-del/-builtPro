"""
Enterprise-ready analytics engine wrapper.

This module handles requests to the analytics engine by extracting the
project identifier and query from the incoming message and delegating
processing to the underlying analytics service defined in
``backend.backend.services.analytics_service``.  It returns a structured
response containing the service name and result.  Any exceptions are
logged and a generic error message is returned to the caller.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .intent_router import router

try:
    # Import the underlying analytics implementation
    from backend.backend.services import analytics_service
except Exception:
    analytics_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

from .rag_engine import _extract_project_id, _extract_query  # reuse helpers


def handle_analytics_engine(message: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle incoming messages for the analytics engine."""
    context = context or {}
    project_id = _extract_project_id(message, context)
    query = _extract_query(message)
    try:
        if analytics_service is None:
            raise RuntimeError("Analytics service implementation is unavailable")
        result = analytics_service.query_logs(project_id, query)
    except Exception as exc:
        logger.exception("Analytics engine error: %s", exc)
        result = "An error occurred while processing your request."
    return {"service": "analytics_engine", "result": result}


# Register service on import
router.register(
    "analytics_engine",
    [r"\banalytics\b", r"\bkpi\b"],
    handle_analytics_engine,
)
