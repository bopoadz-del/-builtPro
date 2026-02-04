"""Meeting summarization helpers."""

from __future__ import annotations

from typing import Dict, List


def summarize_transcript(transcript: str) -> Dict[str, object]:
    if not transcript.strip():
        return {"summary": "", "decisions": [], "action_items": [], "issues": []}

    decisions: List[dict] = []
    action_items: List[dict] = []
    issues: List[dict] = []
    lines = [line.strip() for line in transcript.splitlines() if line.strip()]

    for line in lines:
        lower = line.lower()
        if "decision:" in lower:
            decision_text = line.split(":", 1)[1].strip()
            decisions.append({"description": decision_text})
        if "action assigned to" in lower:
            parts = line.split("Action assigned to", 1)[1].strip().split(" ", 1)
            owner = parts[0]
            description = parts[1] if len(parts) > 1 else line
            action_items.append({"owner": owner, "description": description})
        if "issue:" in lower:
            issue_text = line.split(":", 1)[1].strip()
            severity = "high" if "critical" in lower else "medium"
            issues.append({"description": issue_text, "severity": severity})

    summary_text = "Key decisions and action items captured."
    return {
        "summary": summary_text,
        "decisions": decisions,
        "action_items": action_items,
        "issues": issues,
    }
