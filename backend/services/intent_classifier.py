"""Intent classifier stub."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Classifier:
    def predict(self, text: str) -> tuple[str, float]:
        return "general", 0.5


classifier = _Classifier()
