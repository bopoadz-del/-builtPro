"""Action Item Extraction API endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.services.action_item_extractor import (
    ActionItem,
    ExtractionResult,
    Priority,
    Status,
    extract_actions,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ExtractRequest(BaseModel):
    """Request body for action item extraction."""
    content: str
    use_ai: bool = True
    project_id: Optional[str] = None


class ActionItemResponse(BaseModel):
    """Single action item response."""
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    category: Optional[str] = None
    dependencies: list[str] = []
    source_context: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Full extraction result response."""
    action_items: list[ActionItemResponse]
    summary: str
    meeting_date: Optional[str] = None
    attendees: list[str] = []
    decisions: list[str] = []
    risks: list[str] = []
    total_items: int


@router.get("/action_item_extractor-ping")
async def ping():
    """Health check endpoint."""
    return {"service": "action_item_extractor", "status": "ok"}


@router.post("/extract", response_model=ExtractionResponse)
async def extract_from_text(request: ExtractRequest):
    """Extract action items from meeting minutes text.
    
    Uses OpenAI for intelligent extraction with fallback to rule-based parsing.
    Returns structured action items with assignees, due dates, and priorities.
    """
    try:
        result = extract_actions(
            text=request.content,
            use_ai=request.use_ai
        )
        
        action_items = [
            ActionItemResponse(
                description=item.description,
                assignee=item.assignee,
                due_date=item.due_date,
                priority=item.priority.value,
                status=item.status.value,
                category=item.category,
                dependencies=item.dependencies,
                source_context=item.source_context
            )
            for item in result.action_items
        ]
        
        return ExtractionResponse(
            action_items=action_items,
            summary=result.summary,
            meeting_date=result.meeting_date,
            attendees=result.attendees,
            decisions=result.decisions,
            risks=result.risks,
            total_items=len(action_items)
        )
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract/upload", response_model=ExtractionResponse)
async def extract_from_upload(
    file: UploadFile = File(...),
    use_ai: bool = Form(True),
    project_id: Optional[str] = Form(None)
):
    """Extract action items from uploaded meeting minutes file.
    
    Supports: TXT, PDF (text), DOCX (text), and other text formats.
    """
    try:
        # Read file content
        content_bytes = await file.read()
        
        # Try to decode as text
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = content_bytes.decode('latin-1')
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Could not decode file content. Please upload a text-based document."
                )
        
        result = extract_actions(text=content, use_ai=use_ai)
        
        action_items = [
            ActionItemResponse(
                description=item.description,
                assignee=item.assignee,
                due_date=item.due_date,
                priority=item.priority.value,
                status=item.status.value,
                category=item.category,
                dependencies=item.dependencies,
                source_context=item.source_context
            )
            for item in result.action_items
        ]
        
        return ExtractionResponse(
            action_items=action_items,
            summary=result.summary,
            meeting_date=result.meeting_date,
            attendees=result.attendees,
            decisions=result.decisions,
            risks=result.risks,
            total_items=len(action_items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract/batch")
async def extract_batch(requests: list[ExtractRequest]):
    """Extract action items from multiple documents.
    
    Limited to 5 documents per request.
    Returns aggregated action items across all documents.
    """
    if len(requests) > 5:
        raise HTTPException(
            status_code=400,
            detail="Batch limited to 5 documents per request"
        )
    
    all_action_items: list[ActionItemResponse] = []
    all_decisions: list[str] = []
    all_risks: list[str] = []
    all_attendees: set[str] = set()
    
    for idx, req in enumerate(requests):
        try:
            result = extract_actions(text=req.content, use_ai=req.use_ai)
            
            for item in result.action_items:
                all_action_items.append(ActionItemResponse(
                    description=item.description,
                    assignee=item.assignee,
                    due_date=item.due_date,
                    priority=item.priority.value,
                    status=item.status.value,
                    category=item.category,
                    dependencies=item.dependencies,
                    source_context=f"[Doc {idx+1}] {item.source_context}" if item.source_context else None
                ))
            
            all_decisions.extend(result.decisions)
            all_risks.extend(result.risks)
            all_attendees.update(result.attendees)
            
        except Exception as e:
            logger.warning(f"Batch item {idx} failed: {e}")
    
    return {
        "action_items": all_action_items,
        "decisions": list(set(all_decisions))[:10],
        "risks": list(set(all_risks))[:10],
        "attendees": list(all_attendees),
        "total_items": len(all_action_items),
        "documents_processed": len(requests)
    }


@router.get("/priorities")
async def list_priorities():
    """List available priority levels."""
    return {
        "priorities": [
            {"value": p.value, "name": p.name}
            for p in Priority
        ]
    }


@router.get("/categories")
async def list_categories():
    """List common action item categories for construction projects."""
    return {
        "categories": [
            "Design",
            "Procurement", 
            "Construction",
            "Safety",
            "Quality",
            "Finance",
            "Coordination",
            "Other"
        ]
    }
