"""Chat API endpoints."""

from __future__ import annotations

from typing import List, Tuple

from fastapi import APIRouter, Form

from backend.services.vector_memory import get_active_project

router = APIRouter(prefix="/chat")


def _extract_documents(raw_docs: List[List[str]] | None) -> List[str]:
    if not raw_docs:
        return []
    return [doc for group in raw_docs for doc in group]


def _generate_ai_response(message: str, context_docs: List[str]) -> Tuple[str, float]:
    base_response = "AI response"
    if context_docs:
        base_response += " with citations"
    return base_response, 0.75


@router.post("")
async def chat(message: str = Form(...)):
    active = get_active_project()
    project_id = active.id if active else None
    context_docs: List[str] = []
    if active and active.collection is not None:
        results = active.collection.query(query_texts=[message], n_results=3)
        context_docs = _extract_documents(results.get("documents"))

    response, confidence = _generate_ai_response(message, context_docs)
    if project_id:
        response = f"{response} for project {project_id}"

    return {
        "project_id": project_id,
        "context_docs": context_docs,
        "intent": {"project_id": project_id},
        "response": response,
        "confidence": confidence,
    }
