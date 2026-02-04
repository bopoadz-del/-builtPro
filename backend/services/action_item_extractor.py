"""Action item extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List, Optional


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionItem:
    description: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    category: Optional[str] = None


@dataclass
class ExtractionResult:
    action_items: List[ActionItem] = field(default_factory=list)
    summary: str = ""
    attendees: List[str] = field(default_factory=list)


def _detect_priority(text: str) -> Priority:
    lowered = text.lower()
    if "urgent" in lowered or "asap" in lowered or "immediately" in lowered:
        return Priority.CRITICAL
    if "high" in lowered:
        return Priority.HIGH
    return Priority.MEDIUM


def _detect_due_date(text: str) -> Optional[str]:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if match:
        return match.group(1)
    match = re.search(r"by\s+([A-Za-z]+\s+\d{1,2})", text)
    if match:
        return match.group(1)
    match = re.search(r"by\s+next\s+([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        return f"next {match.group(1)}"
    return None


def _detect_category(text: str) -> Optional[str]:
    lowered = text.lower()
    if "design" in lowered or "drawings" in lowered:
        return "design"
    if "procurement" in lowered or "order" in lowered:
        return "procurement"
    if "safety" in lowered:
        return "safety"
    if "qa" in lowered:
        return "qa"
    return None


def extract_actions(text: str, use_ai: bool = False) -> ExtractionResult:  # noqa: ARG001
    if not text.strip():
        return ExtractionResult(action_items=[], summary="No action items found.")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    action_items: List[ActionItem] = []
    attendees: List[str] = []

    for line in lines:
        if "attendees" in line.lower():
            attendees.extend([name.strip() for name in line.split(":", 1)[-1].split(",") if name.strip()])
        if re.search(r"action|will|needs to|should|urgent|asap|must|task", line, re.IGNORECASE):
            owner_match = re.search(r"^(\w+)", line)
            owner = owner_match.group(1) if owner_match else None
            action_items.append(
                ActionItem(
                    description=line,
                    owner=owner,
                    due_date=_detect_due_date(line),
                    priority=_detect_priority(line),
                    category=_detect_category(line),
                )
            )

    summary = "Extracted action items and attendees."
    return ExtractionResult(action_items=action_items, summary=summary, attendees=attendees)


def extract_action_items(text: str, use_ai: bool = False) -> ExtractionResult:  # noqa: ARG001
    return extract_actions(text, use_ai=use_ai)
