from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .intent_router import router

logger = logging.getLogger(__name__)


def _extract_project_id(message: Any, context: Optional[Dict[str, Any]] = None) -> str:
    """Extract project_id from context or message."""
    context = context or {}
    # Context project_id takes precedence
    if context.get("project_id"):
        return context["project_id"]
    # Try to extract from message dict
    if isinstance(message, dict):
        return message.get("project_id", "")
    return ""


def _extract_query(message: Any) -> str:
    """Extract query text from message."""
    if isinstance(message, dict):
        # Try common fields
        for key in ["content", "text", "query", "message"]:
            if key in message and isinstance(message[key], str):
                return message[key]
    if isinstance(message, str):
        return message
    return ""


def handle_rag_engine(message: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle RAG (Retrieval Augmented Generation) requests."""
    context = context or {}
    project_id = _extract_project_id(message, context)
    query = _extract_query(message)
    
    try:
        # For now, return a stub response
        # In production, this would query vector store and generate response
        result = f"RAG search for: {query}" if query else "No query provided"
    except Exception as exc:
        logger.exception("RAG engine error: %s", exc)
        result = "An error occurred while processing your request."
    
    return {"service": "rag_engine", "result": result}


# Register service on import
router.register("rag_engine", [r"\brag\b", r"\bsearch\b", r"\bmemory\b"], handle_rag_engine)
