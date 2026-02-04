"""Minimal intent router used by service wrappers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Pattern
import re


Handler = Callable[[Any, Dict[str, Any] | None], Dict[str, Any]]


@dataclass
class IntentRouter:
    registry: Dict[str, Handler] = field(default_factory=dict)
    patterns: Dict[str, List[Pattern[str]]] = field(default_factory=dict)

    def register(self, name: str, pattern_list: List[str], handler: Handler) -> None:
        self.registry[name] = handler
        compiled = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
        self.patterns[name] = compiled


router = IntentRouter()
