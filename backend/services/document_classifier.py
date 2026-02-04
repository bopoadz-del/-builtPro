"""Document classification helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class DocumentType(str, Enum):
    CONTRACT = "Contract"
    DRAWING = "Drawing"
    SPECIFICATION = "Specification"
    RFI = "RFI"
    SUBMITTAL = "Submittal"
    CHANGE_ORDER = "Change Order"
    MEETING_MINUTES = "Meeting Minutes"
    INVOICE = "Invoice"
    SCHEDULE = "Schedule"
    REPORT = "Report"
    CORRESPONDENCE = "Correspondence"
    PERMIT = "Permit"
    SAFETY_DOCUMENT = "Safety Document"
    QA_QC_DOCUMENT = "QA/QC Document"
    UNKNOWN = "Unknown"


@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float
    summary: Optional[str] = None


def _summarize(content: str) -> str:
    return content.strip().split("\n")[0][:200] if content.strip() else ""


def classify_document(content: str, filename: str | None = None, use_ai: bool = False) -> ClassificationResult:  # noqa: ARG001
    text = content.lower()
    if not text.strip():
        return ClassificationResult(DocumentType.UNKNOWN, 0.0, summary="")

    if "meeting minutes" in text:
        return ClassificationResult(DocumentType.MEETING_MINUTES, 0.8, summary=_summarize(content))
    if "invoice" in text:
        return ClassificationResult(DocumentType.INVOICE, 0.6, summary=_summarize(content))
    if "rfi" in text:
        return ClassificationResult(DocumentType.RFI, 0.6, summary=_summarize(content))
    if "agreement" in text or "contract" in text:
        return ClassificationResult(DocumentType.CONTRACT, 0.4, summary=_summarize(content))

    if filename:
        ext = Path(filename).suffix.lower()
        if ext in {".dwg", ".dxf"}:
            return ClassificationResult(DocumentType.DRAWING, 0.5, summary=_summarize(content))

    return ClassificationResult(DocumentType.REPORT, 0.5, summary=_summarize(content))


def classify_document_file(path: str, use_ai: bool = False) -> ClassificationResult:  # noqa: ARG001
    content = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    return classify_document(content, filename=path, use_ai=use_ai)
