"""PDP schemas and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Role(str, Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class PolicyType(str, Enum):
    RBAC = "rbac"
    ABAC = "abac"
    HYBRID = "hybrid"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatternType(str, Enum):
    PII = "pii"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    MALICIOUS = "malicious"


@dataclass
class PolicyRequest:
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int]
    context: Dict[str, Any]


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
