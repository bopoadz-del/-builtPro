"""Lightweight intent classifier for Render environments."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _joblib_module():
    return None


@lru_cache(maxsize=1)
def _tfidf_resources():
    return None


@lru_cache(maxsize=1)
def _bert_pipeline():
    return None


def classify_intent(text: str) -> dict:
    lowered = text.lower()
    if "approve" in lowered:
        return {"intent": "APPROVAL", "source": "rule", "confidence": 1.0}
    return {"intent": "GENERAL", "source": "fallback", "confidence": 0.5}
