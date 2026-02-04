"""Document Classification Service using OpenAI.

Classifies construction documents into predefined categories with confidence scores.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Construction document types for classification."""
    CONTRACT = "Contract"
    DRAWING = "Drawing"
    SPECIFICATION = "Specification"
    RFI = "RFI"  # Request for Information
    SUBMITTAL = "Submittal"
    CHANGE_ORDER = "Change Order"
    MEETING_MINUTES = "Meeting Minutes"
    INVOICE = "Invoice"
    SCHEDULE = "Schedule"
    REPORT = "Report"
    CORRESPONDENCE = "Correspondence"
    PERMIT = "Permit"
    SAFETY = "Safety Document"
    QA_QC = "QA/QC Document"
    UNKNOWN = "Unknown"


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: DocumentType
    confidence: float
    sub_type: Optional[str] = None
    key_entities: Optional[list[str]] = None
    summary: Optional[str] = None


# Few-shot examples for classification
CLASSIFICATION_EXAMPLES = """
Example 1:
Content: "This Agreement is entered into as of January 15, 2024, by and between ABC Construction LLC ("Contractor") and Diriyah Company ("Owner"). The Contractor agrees to perform the Work described in Exhibit A for a Contract Sum of SAR 45,000,000..."
Classification: Contract
Confidence: 0.95
Sub-type: Construction Agreement

Example 2:
Content: "RFI #2024-0156. Project: Heritage Quarter Phase 2. Subject: Foundation Detail Clarification. We request clarification on the foundation reinforcement details shown on Drawing S-101..."
Classification: RFI
Confidence: 0.98
Sub-type: Structural RFI

Example 3:
Content: "Meeting Minutes - Weekly Progress Meeting. Date: March 15, 2024. Attendees: John Smith (PM), Ahmed Hassan (Site Engineer)... Action Items: 1. John to submit revised schedule by Friday..."
Classification: Meeting Minutes
Confidence: 0.97
Sub-type: Progress Meeting

Example 4:
Content: "INVOICE #INV-2024-0892. Bill To: Diriyah Company. From: Gulf Steel Suppliers. Date: March 20, 2024. Description: Reinforcement Steel Grade 60 - 500 tons @ SAR 2,800/ton..."
Classification: Invoice
Confidence: 0.96
Sub-type: Material Invoice

Example 5:
Content: "SUBMITTAL #SUB-2024-0234. Project: Gateway Villas. Specification Section: 03 30 00 - Cast-in-Place Concrete. Product: Ready-Mix Concrete C40/50. Manufacturer: Saudi Ready Mix..."
Classification: Submittal
Confidence: 0.95
Sub-type: Material Submittal
"""

SYSTEM_PROMPT = f"""You are a construction document classification expert. Your task is to classify documents into one of these categories:

Categories:
- Contract: Legal agreements, contracts, amendments
- Drawing: Architectural, structural, MEP drawings
- Specification: Technical specifications, standards
- RFI: Request for Information documents
- Submittal: Product submittals, shop drawings
- Change Order: Change orders, variations
- Meeting Minutes: Meeting notes, minutes
- Invoice: Invoices, payment certificates
- Schedule: Project schedules, Gantt charts
- Report: Progress reports, inspection reports
- Correspondence: Letters, emails, memos
- Permit: Building permits, approvals
- Safety Document: Safety plans, incident reports
- QA/QC Document: Quality control documents, test reports
- Unknown: Cannot be classified

{CLASSIFICATION_EXAMPLES}

Respond ONLY with a JSON object in this exact format:
{{
    "document_type": "<category>",
    "confidence": <0.0-1.0>,
    "sub_type": "<specific type or null>",
    "key_entities": ["<entity1>", "<entity2>"],
    "summary": "<one sentence summary>"
}}"""


def _get_openai_client():
    """Get OpenAI client if available."""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        openai.api_key = api_key
        return openai
    except ImportError:
        logger.warning("OpenAI package not installed")
        return None


def _classify_with_openai(content: str, filename: Optional[str] = None) -> ClassificationResult:
    """Classify document using OpenAI API."""
    openai = _get_openai_client()
    if openai is None:
        raise RuntimeError("OpenAI not available")
    
    user_content = f"Classify this construction document:\n\nFilename: {filename or 'unknown'}\n\nContent:\n{content[:4000]}"
    
    try:
        # Try new client API first (openai >= 1.0)
        if hasattr(openai, 'OpenAI'):
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=500
            )
            result_text = response.choices[0].message.content
        else:
            # Fallback to legacy API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=500
            )
            result_text = response.choices[0].message.content
        
        # Parse JSON response
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        data = json.loads(result_text)
        
        doc_type_str = data.get("document_type", "Unknown")
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            doc_type = DocumentType.UNKNOWN
        
        return ClassificationResult(
            document_type=doc_type,
            confidence=float(data.get("confidence", 0.5)),
            sub_type=data.get("sub_type"),
            key_entities=data.get("key_entities", []),
            summary=data.get("summary")
        )
        
    except Exception as e:
        logger.error(f"OpenAI classification failed: {e}")
        raise


def _classify_with_rules(content: str, filename: Optional[str] = None) -> ClassificationResult:
    """Fallback rule-based classification when OpenAI is unavailable."""
    content_lower = content.lower()
    filename_lower = (filename or "").lower()
    
    # Rule-based classification
    rules = [
        (DocumentType.CONTRACT, ["agreement", "contract", "hereby", "parties", "witnesseth"], 0.75),
        (DocumentType.RFI, ["rfi", "request for information", "clarification requested"], 0.85),
        (DocumentType.INVOICE, ["invoice", "bill to", "payment", "amount due", "total:"], 0.80),
        (DocumentType.MEETING_MINUTES, ["meeting minutes", "attendees:", "action items", "meeting notes"], 0.85),
        (DocumentType.SUBMITTAL, ["submittal", "shop drawing", "product data", "manufacturer"], 0.80),
        (DocumentType.CHANGE_ORDER, ["change order", "variation", "modification", "co #"], 0.85),
        (DocumentType.DRAWING, ["drawing", "dwg", "detail", "section", "elevation", "plan"], 0.70),
        (DocumentType.SPECIFICATION, ["specification", "section", "scope", "materials", "execution"], 0.75),
        (DocumentType.SCHEDULE, ["schedule", "gantt", "milestone", "baseline", "critical path"], 0.80),
        (DocumentType.REPORT, ["report", "progress", "status", "summary", "findings"], 0.70),
        (DocumentType.PERMIT, ["permit", "approval", "license", "authorization"], 0.80),
        (DocumentType.SAFETY, ["safety", "incident", "hazard", "ppe", "toolbox"], 0.85),
        (DocumentType.QA_QC, ["qa/qc", "quality", "inspection", "test report", "ncr"], 0.80),
        (DocumentType.CORRESPONDENCE, ["dear", "regards", "sincerely", "re:", "subject:"], 0.60),
    ]
    
    best_match = DocumentType.UNKNOWN
    best_confidence = 0.0
    matched_keywords = []
    
    for doc_type, keywords, base_confidence in rules:
        matches = [kw for kw in keywords if kw in content_lower or kw in filename_lower]
        if matches:
            confidence = base_confidence * (len(matches) / len(keywords))
            confidence = min(confidence * 1.2, 0.95)  # Boost but cap at 0.95
            if confidence > best_confidence:
                best_match = doc_type
                best_confidence = confidence
                matched_keywords = matches
    
    return ClassificationResult(
        document_type=best_match,
        confidence=round(best_confidence, 2) if best_confidence > 0 else 0.3,
        sub_type=None,
        key_entities=matched_keywords[:5],
        summary=f"Document classified as {best_match.value} based on keyword matching"
    )


def classify_document(
    content: str,
    filename: Optional[str] = None,
    use_ai: bool = True
) -> ClassificationResult:
    """Classify a construction document.
    
    Args:
        content: Document text content
        filename: Optional filename for additional context
        use_ai: Whether to use OpenAI (falls back to rules if unavailable)
    
    Returns:
        ClassificationResult with type, confidence, and metadata
    """
    if not content or not content.strip():
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            summary="Empty document content"
        )
    
    if use_ai:
        try:
            return _classify_with_openai(content, filename)
        except Exception as e:
            logger.warning(f"AI classification failed, falling back to rules: {e}")
    
    return _classify_with_rules(content, filename)


def classify_document_file(file_path: str, use_ai: bool = True) -> ClassificationResult:
    """Classify a document from file path.
    
    Args:
        file_path: Path to the document file
        use_ai: Whether to use OpenAI
    
    Returns:
        ClassificationResult
    """
    import os
    
    if not os.path.exists(file_path):
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            summary=f"File not found: {file_path}"
        )
    
    filename = os.path.basename(file_path)
    
    # Try to extract text based on file type
    try:
        from backend.services.extract_text import extract_text
        content = extract_text(file_path)
    except ImportError:
        # Fallback: read as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                summary=f"Could not read file: {e}"
            )
    
    return classify_document(content, filename, use_ai)


__all__ = [
    "DocumentType",
    "ClassificationResult", 
    "classify_document",
    "classify_document_file"
]
