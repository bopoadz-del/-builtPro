"""Universal Linking Engine (ULE) / Pack System for construction document linking."""

from backend.reasoning.schemas import (
    Entity,
    EntityType,
    Evidence,
    EvidenceType,
    Link,
    LinkRequest,
    LinkResult,
    LinkType,
    PackConfig,
    DocumentInput,
)

try:
    from backend.reasoning.ule_engine import ULEEngine
except Exception:  # pragma: no cover - numpy may be absent in lightweight deploys
    ULEEngine = None  # type: ignore[assignment,misc]

__all__ = [
    "Entity",
    "EntityType",
    "Evidence",
    "EvidenceType",
    "Link",
    "LinkRequest",
    "LinkResult",
    "LinkType",
    "PackConfig",
    "DocumentInput",
    "ULEEngine",
]
