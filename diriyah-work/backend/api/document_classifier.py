"""Document Classification API endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.services.document_classifier import (
    ClassificationResult,
    DocumentType,
    classify_document,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ClassifyTextRequest(BaseModel):
    """Request body for text classification."""
    content: str
    filename: Optional[str] = None
    use_ai: bool = True


class ClassificationResponse(BaseModel):
    """Classification result response."""
    document_type: str
    confidence: float
    sub_type: Optional[str] = None
    key_entities: list[str] = []
    summary: Optional[str] = None


class BatchClassificationResponse(BaseModel):
    """Response for batch classification."""
    results: list[ClassificationResponse]
    total: int
    successful: int


@router.get("/document_classifier-ping")
async def ping():
    """Health check endpoint."""
    return {"service": "document_classifier", "status": "ok"}


@router.get("/document-types")
async def list_document_types():
    """List all supported document types."""
    return {
        "types": [
            {"value": dt.value, "name": dt.name}
            for dt in DocumentType
            if dt != DocumentType.UNKNOWN
        ]
    }


@router.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassifyTextRequest):
    """Classify document from text content.
    
    Uses OpenAI for intelligent classification with fallback to rule-based.
    """
    try:
        result = classify_document(
            content=request.content,
            filename=request.filename,
            use_ai=request.use_ai
        )
        
        return ClassificationResponse(
            document_type=result.document_type.value,
            confidence=result.confidence,
            sub_type=result.sub_type,
            key_entities=result.key_entities or [],
            summary=result.summary
        )
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/classify/upload", response_model=ClassificationResponse)
async def classify_upload(
    file: UploadFile = File(...),
    use_ai: bool = Form(True)
):
    """Classify an uploaded document file.
    
    Supports: PDF, DOCX, TXT, and other text-based formats.
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
        
        result = classify_document(
            content=content,
            filename=file.filename,
            use_ai=use_ai
        )
        
        return ClassificationResponse(
            document_type=result.document_type.value,
            confidence=result.confidence,
            sub_type=result.sub_type,
            key_entities=result.key_entities or [],
            summary=result.summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch(requests: list[ClassifyTextRequest]):
    """Classify multiple documents in batch.
    
    Limited to 10 documents per request.
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Batch limited to 10 documents per request"
        )
    
    results = []
    successful = 0
    
    for req in requests:
        try:
            result = classify_document(
                content=req.content,
                filename=req.filename,
                use_ai=req.use_ai
            )
            results.append(ClassificationResponse(
                document_type=result.document_type.value,
                confidence=result.confidence,
                sub_type=result.sub_type,
                key_entities=result.key_entities or [],
                summary=result.summary
            ))
            successful += 1
        except Exception as e:
            logger.warning(f"Batch item failed: {e}")
            results.append(ClassificationResponse(
                document_type=DocumentType.UNKNOWN.value,
                confidence=0.0,
                summary=f"Classification failed: {str(e)}"
            ))
    
    return BatchClassificationResponse(
        results=results,
        total=len(requests),
        successful=successful
    )
