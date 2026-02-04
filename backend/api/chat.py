"""Chat API with RAG-based citations and OpenAI integration."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, Body, Form, HTTPException, Request
from pydantic import BaseModel

try:  # pragma: no cover - optional multipart dependency
    import multipart  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled gracefully
    multipart = None  # type: ignore[assignment]

_message_dependency = Form(None) if multipart is not None else Body(None)

from backend.services.intent_router import IntentRouter
from backend.services.vector_memory import get_active_project

logger = logging.getLogger(__name__)
router = APIRouter()
intent_router = IntentRouter()


@dataclass
class Citation:
    """Source citation for a chat response."""
    document_id: str
    document_name: str
    snippet: str
    relevance_score: float
    page: Optional[int] = None


class ChatRequest(BaseModel):
    """Structured chat request."""
    message: str
    project_id: Optional[str] = None
    include_citations: bool = True
    max_citations: int = 3


class ChatResponse(BaseModel):
    """Structured chat response with citations."""
    response: str
    intent: dict
    project_id: Optional[str]
    citations: list[dict] = []
    confidence: float = 0.0


def _get_openai_client():
    """Get OpenAI client if available."""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return openai
    except ImportError:
        return None


def _generate_ai_response(
    message: str,
    context_docs: list[str],
    project_context: Optional[dict] = None
) -> tuple[str, float]:
    """Generate AI response using OpenAI with document context."""
    openai = _get_openai_client()
    
    if openai is None:
        # Fallback response when OpenAI is not available
        if context_docs:
            return (
                f"Based on the project documents, I found {len(context_docs)} relevant sources. "
                f"Key excerpt: '{context_docs[0][:200]}...' "
                "For a more detailed AI analysis, please configure the OpenAI API key.",
                0.6
            )
        return (
            "I understand your question. However, I couldn't find specific documents "
            "related to your query in the current project context. Could you provide more details "
            "or upload relevant documents?",
            0.4
        )
    
    # Build context for the AI
    system_prompt = """You are Diriyah Brain AI, an intelligent assistant for construction project management.
You help project managers, engineers, and stakeholders by:
- Answering questions about project documents, specifications, and requirements
- Extracting key information from contracts, drawings, and reports
- Providing insights based on project data
- Helping track progress, costs, and risks

When answering:
1. Be specific and cite relevant document sections when available
2. If information is from a document, mention which document
3. Be concise but thorough
4. If you're not sure, say so and suggest what information might help
5. Use construction industry terminology appropriately

Current context: You have access to project documents through RAG (Retrieval Augmented Generation)."""

    # Add project context
    if project_context:
        system_prompt += f"\n\nActive Project: {project_context.get('name', 'Unknown')}"
        system_prompt += f"\nProject ID: {project_context.get('id', 'N/A')}"
    
    # Build context from retrieved documents
    context_text = ""
    if context_docs:
        context_text = "\n\nRelevant document excerpts:\n"
        for i, doc in enumerate(context_docs[:5], 1):
            context_text += f"\n[Source {i}]: {doc[:500]}"
    
    user_message = message
    if context_text:
        user_message = f"{message}\n{context_text}"
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Try new client API first (openai >= 1.0)
        if hasattr(openai, 'OpenAI'):
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            ai_response = response.choices[0].message.content
            confidence = 0.85 if context_docs else 0.7
        else:
            # Fallback to legacy API
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            ai_response = response.choices[0].message.content
            confidence = 0.85 if context_docs else 0.7
        
        return ai_response, confidence
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return (
            f"I encountered an issue generating a response: {str(e)}. "
            "Please try again or contact support if the issue persists.",
            0.3
        )


def _extract_citations(
    query: str,
    collection: Any,
    max_results: int = 3
) -> tuple[list[str], list[Citation]]:
    """Extract relevant documents and format as citations."""
    context_docs: list[str] = []
    citations: list[Citation] = []
    
    if collection is None or not hasattr(collection, "query"):
        return context_docs, citations
    
    try:
        result = collection.query(
            query_texts=[query],
            n_results=max_results,
            include=["documents", "metadatas", "distances"]
        )
        
        if not isinstance(result, Mapping):
            return context_docs, citations
        
        documents = result.get("documents", [[]])
        metadatas = result.get("metadatas", [[]])
        distances = result.get("distances", [[]])
        
        if documents and isinstance(documents[0], list):
            docs = documents[0]
            metas = metadatas[0] if metadatas and metadatas[0] else [{}] * len(docs)
            dists = distances[0] if distances and distances[0] else [0.5] * len(docs)
            
            for i, doc in enumerate(docs):
                if doc:
                    context_docs.append(doc)
                    
                    meta = metas[i] if i < len(metas) else {}
                    dist = dists[i] if i < len(dists) else 0.5
                    
                    # Convert distance to relevance score (lower distance = higher relevance)
                    relevance = max(0.0, 1.0 - dist)
                    
                    citations.append(Citation(
                        document_id=meta.get("id", f"doc_{i}"),
                        document_name=meta.get("filename", meta.get("name", f"Document {i+1}")),
                        snippet=doc[:300] + "..." if len(doc) > 300 else doc,
                        relevance_score=round(relevance, 2),
                        page=meta.get("page")
                    ))
    
    except Exception as e:
        logger.warning(f"Citation extraction failed: {e}")
    
    return context_docs, citations


@router.post("/chat")
async def chat(request: Request, message: Optional[str] = _message_dependency) -> dict[str, Any]:
    """Respond to chat messages with AI-powered answers and document citations.
    
    Features:
    - Intent classification for routing queries
    - RAG-based document retrieval for context
    - OpenAI-powered response generation
    - Source citations with relevance scores
    """
    
    content_type = request.headers.get("content-type", "")
    include_citations = True
    max_citations = 3
    
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = None
        if isinstance(payload, Mapping):
            potential = payload.get("message")
            if isinstance(potential, str):
                message = potential
            include_citations = payload.get("include_citations", True)
            max_citations = payload.get("max_citations", 3)
    else:
        if multipart is None:
            try:
                raw_body = (await request.body()).decode("utf-8")
            except Exception:
                raw_body = ""
            parsed = parse_qs(raw_body)
            values = parsed.get("message")
            if values and isinstance(values, list):
                first = values[0]
                if isinstance(first, str):
                    message = first
        else:
            try:
                form = await request.form()
            except Exception:
                form = None
            if form is not None:
                potential = form.get("message")
                if isinstance(potential, str):
                    message = potential

    if not message:
        raise HTTPException(status_code=400, detail="message parameter is required")

    # Get active project context
    active = get_active_project()
    project_id = None
    collection = None
    project_context = None

    if isinstance(active, Mapping):
        project_id = active.get("id")
        collection = active.get("collection")
        project_context = {"id": project_id, "name": active.get("name", "Unknown Project")}
    elif active is not None:
        project_id = getattr(active, "id", None)
        collection = getattr(active, "collection", None)
        project_context = {"id": project_id, "name": getattr(active, "name", "Unknown Project")}

    # Classify intent
    intent_result = intent_router.route(message, project_id=project_id)

    # Extract relevant documents and citations
    context_docs, citations = _extract_citations(
        message, 
        collection, 
        max_results=max_citations if include_citations else 0
    )

    # Generate AI response
    ai_response, confidence = _generate_ai_response(
        message,
        context_docs,
        project_context
    )

    return {
        "response": ai_response,
        "intent": intent_result,
        "project_id": project_id,
        "citations": [
            {
                "document_id": c.document_id,
                "document_name": c.document_name,
                "snippet": c.snippet,
                "relevance_score": c.relevance_score,
                "page": c.page
            }
            for c in citations
        ] if include_citations else [],
        "confidence": confidence,
        "context_docs_count": len(context_docs),
        **({"context_docs": context_docs} if include_citations else {}),
    }


@router.post("/chat/structured", response_model=ChatResponse)
async def chat_structured(request: ChatRequest) -> ChatResponse:
    """Structured chat endpoint with full request/response models.
    
    Provides the same functionality as /chat but with explicit request/response types
    for better API documentation and client code generation.
    """
    # Get active project context
    active = get_active_project()
    project_id = request.project_id
    collection = None
    project_context = None
    
    if isinstance(active, Mapping):
        if project_id is None:
            project_id = active.get("id")
        collection = active.get("collection")
        project_context = {"id": project_id, "name": active.get("name", "Unknown Project")}
    elif active is not None:
        if project_id is None:
            project_id = getattr(active, "id", None)
        collection = getattr(active, "collection", None)
        project_context = {"id": project_id, "name": getattr(active, "name", "Unknown Project")}
    
    # Classify intent
    intent_result = intent_router.route(request.message, project_id=project_id)
    
    # Extract relevant documents and citations
    context_docs, citations = _extract_citations(
        request.message,
        collection,
        max_results=request.max_citations if request.include_citations else 0
    )
    
    # Generate AI response
    ai_response, confidence = _generate_ai_response(
        request.message,
        context_docs,
        project_context
    )
    
    return ChatResponse(
        response=ai_response,
        intent=intent_result,
        project_id=project_id,
        citations=[
            {
                "document_id": c.document_id,
                "document_name": c.document_name,
                "snippet": c.snippet,
                "relevance_score": c.relevance_score,
                "page": c.page
            }
            for c in citations
        ] if request.include_citations else [],
        confidence=confidence
    )


@router.post("/chat/context")
async def chat_with_context(
    message: str = Body(...),
    context: str = Body(...),
    project_id: Optional[str] = Body(None)
) -> dict[str, Any]:
    """Chat with explicit context provided (bypass RAG).
    
    Useful for:
    - Asking questions about specific document content
    - Testing without vector database
    - Providing custom context for the AI
    """
    project_context = {"id": project_id} if project_id else None
    
    # Intent classification
    intent_result = intent_router.route(message, project_id=project_id)
    
    # Generate response with provided context
    ai_response, confidence = _generate_ai_response(
        message,
        [context] if context else [],
        project_context
    )
    
    return {
        "response": ai_response,
        "intent": intent_result,
        "project_id": project_id,
        "confidence": confidence,
        "context_provided": True
    }
