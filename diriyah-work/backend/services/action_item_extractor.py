"""Action Item Extraction Service using OpenAI.

Extracts structured action items from meeting minutes and other documents.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Priority(str, Enum):
    """Action item priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Action item status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class ActionItem:
    """Structured action item extracted from text."""
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.OPEN
    category: Optional[str] = None  # e.g., "Design", "Procurement", "Safety"
    dependencies: list[str] = field(default_factory=list)
    source_context: Optional[str] = None  # Original text snippet
    
    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "assignee": self.assignee,
            "due_date": self.due_date,
            "priority": self.priority.value,
            "status": self.status.value,
            "category": self.category,
            "dependencies": self.dependencies,
            "source_context": self.source_context
        }


@dataclass
class ExtractionResult:
    """Result of action item extraction."""
    action_items: list[ActionItem]
    summary: str
    meeting_date: Optional[str] = None
    attendees: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


SYSTEM_PROMPT = """You are an expert at extracting action items from construction project meeting minutes and documents.

Extract all action items with the following structure:
- description: Clear, actionable description of the task
- assignee: Person or team responsible (if mentioned)
- due_date: Deadline if mentioned (in YYYY-MM-DD format if possible, or relative like "next Friday")
- priority: critical, high, medium, or low (infer from urgency words)
- category: Design, Procurement, Construction, Safety, Quality, Finance, Coordination, or Other
- dependencies: List any tasks this depends on

Also extract:
- Meeting date (if mentioned)
- Attendees (list of names)
- Key decisions made
- Risks or concerns raised

Respond ONLY with a JSON object in this exact format:
{
    "meeting_date": "YYYY-MM-DD or null",
    "attendees": ["Name1", "Name2"],
    "action_items": [
        {
            "description": "Clear action description",
            "assignee": "Person Name or null",
            "due_date": "YYYY-MM-DD or relative date or null",
            "priority": "critical|high|medium|low",
            "category": "category name",
            "dependencies": [],
            "source_context": "Original sentence mentioning this"
        }
    ],
    "decisions": ["Decision 1", "Decision 2"],
    "risks": ["Risk 1", "Risk 2"],
    "summary": "Brief 1-2 sentence summary of the meeting"
}"""


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


def _extract_with_openai(text: str) -> ExtractionResult:
    """Extract action items using OpenAI API."""
    openai = _get_openai_client()
    if openai is None:
        raise RuntimeError("OpenAI not available")
    
    try:
        # Try new client API first (openai >= 1.0)
        if hasattr(openai, 'OpenAI'):
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract action items from this meeting content:\n\n{text[:6000]}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            result_text = response.choices[0].message.content
        else:
            # Fallback to legacy API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract action items from this meeting content:\n\n{text[:6000]}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            result_text = response.choices[0].message.content
        
        # Parse JSON response
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        data = json.loads(result_text)
        
        action_items = []
        for item in data.get("action_items", []):
            try:
                priority = Priority(item.get("priority", "medium").lower())
            except ValueError:
                priority = Priority.MEDIUM
            
            action_items.append(ActionItem(
                description=item.get("description", ""),
                assignee=item.get("assignee"),
                due_date=item.get("due_date"),
                priority=priority,
                status=Status.OPEN,
                category=item.get("category"),
                dependencies=item.get("dependencies", []),
                source_context=item.get("source_context")
            ))
        
        return ExtractionResult(
            action_items=action_items,
            summary=data.get("summary", ""),
            meeting_date=data.get("meeting_date"),
            attendees=data.get("attendees", []),
            decisions=data.get("decisions", []),
            risks=data.get("risks", [])
        )
        
    except Exception as e:
        logger.error(f"OpenAI extraction failed: {e}")
        raise


def _extract_with_rules(text: str) -> ExtractionResult:
    """Fallback rule-based extraction when OpenAI is unavailable."""
    action_items = []
    decisions = []
    risks = []
    attendees = []
    meeting_date = None
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    
    # Action item patterns
    action_patterns = [
        r'\b(will|shall|must|need to|should|to be)\s+(\w+)',
        r'\baction[:\s]+(.+)',
        r'\bassigned to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'\b(deliver|submit|complete|prepare|review|coordinate|schedule|send)\b',
        r'\bby\s+(next\s+\w+|\w+\s+\d{1,2}|\d{4}-\d{2}-\d{2})',
    ]
    
    # Decision patterns
    decision_patterns = [
        r'\b(decided|agreed|approved|confirmed)\s+(.+)',
        r'\bdecision[:\s]+(.+)',
    ]
    
    # Risk patterns
    risk_patterns = [
        r'\b(risk|concern|issue|blocker|delay)\s*[:\s]+(.+)',
        r'\b(critical|urgent|immediate)\s+(\w+)',
    ]
    
    # Attendee patterns
    attendee_match = re.search(r'attendees?[:\s]+([^\n]+)', text, re.IGNORECASE)
    if attendee_match:
        names = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', attendee_match.group(1))
        attendees = names[:10]
    
    # Date patterns
    date_match = re.search(r'date[:\s]+(\d{4}-\d{2}-\d{2}|\w+\s+\d{1,2},?\s+\d{4})', text, re.IGNORECASE)
    if date_match:
        meeting_date = date_match.group(1)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        lower = sentence.lower()
        
        # Check for action items
        is_action = any(re.search(pattern, lower) for pattern in action_patterns)
        if is_action:
            # Extract assignee
            assignee = None
            assignee_match = re.search(r'(?:assigned to|to )\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', sentence)
            if assignee_match:
                assignee = assignee_match.group(1)
            
            # Extract due date
            due_date = None
            due_match = re.search(r'by\s+(next\s+\w+|\w+\s+\d{1,2}|\d{4}-\d{2}-\d{2})', sentence, re.IGNORECASE)
            if due_match:
                due_date = due_match.group(1)
            
            # Determine priority
            priority = Priority.MEDIUM
            if any(word in lower for word in ['urgent', 'critical', 'immediate', 'asap']):
                priority = Priority.CRITICAL
            elif any(word in lower for word in ['important', 'priority', 'soon']):
                priority = Priority.HIGH
            
            # Determine category
            category = "Other"
            if any(word in lower for word in ['design', 'drawing', 'specification']):
                category = "Design"
            elif any(word in lower for word in ['procure', 'order', 'supplier', 'material']):
                category = "Procurement"
            elif any(word in lower for word in ['construct', 'install', 'build', 'pour']):
                category = "Construction"
            elif any(word in lower for word in ['safety', 'hazard', 'ppe']):
                category = "Safety"
            elif any(word in lower for word in ['quality', 'inspect', 'test', 'qa', 'qc']):
                category = "Quality"
            elif any(word in lower for word in ['cost', 'budget', 'payment', 'invoice']):
                category = "Finance"
            elif any(word in lower for word in ['coordinate', 'meeting', 'schedule']):
                category = "Coordination"
            
            action_items.append(ActionItem(
                description=sentence[:200],
                assignee=assignee,
                due_date=due_date,
                priority=priority,
                category=category,
                source_context=sentence
            ))
        
        # Check for decisions
        if any(re.search(pattern, lower) for pattern in decision_patterns):
            decisions.append(sentence[:200])
        
        # Check for risks
        if any(re.search(pattern, lower) for pattern in risk_patterns):
            risks.append(sentence[:200])
    
    # Generate summary
    summary_parts = []
    if action_items:
        summary_parts.append(f"{len(action_items)} action items identified")
    if decisions:
        summary_parts.append(f"{len(decisions)} decisions made")
    if risks:
        summary_parts.append(f"{len(risks)} risks/concerns raised")
    
    summary = ". ".join(summary_parts) if summary_parts else "No significant items extracted"
    
    return ExtractionResult(
        action_items=action_items,
        summary=summary,
        meeting_date=meeting_date,
        attendees=attendees,
        decisions=decisions[:5],
        risks=risks[:5]
    )


def extract_actions(text: str, use_ai: bool = True) -> ExtractionResult:
    """Extract action items from meeting minutes or document text.
    
    Args:
        text: Meeting minutes or document content
        use_ai: Whether to use OpenAI (falls back to rules if unavailable)
    
    Returns:
        ExtractionResult with action items and metadata
    """
    if not text or not text.strip():
        return ExtractionResult(
            action_items=[],
            summary="No content provided"
        )
    
    if use_ai:
        try:
            return _extract_with_openai(text)
        except Exception as e:
            logger.warning(f"AI extraction failed, falling back to rules: {e}")
    
    return _extract_with_rules(text)


def extract_action_items(text: str, use_ai: bool = True) -> list[ActionItem]:
    """Convenience function to extract just action items.
    
    Args:
        text: Meeting minutes or document content
        use_ai: Whether to use OpenAI
    
    Returns:
        List of ActionItem objects
    """
    result = extract_actions(text, use_ai)
    return result.action_items


__all__ = [
    "Priority",
    "Status", 
    "ActionItem",
    "ExtractionResult",
    "extract_actions",
    "extract_action_items"
]
