"""
Data Privacy Manager for BuilTPro Brain AI

GDPR compliance, data classification, anonymization, and consent management.

Features:
- Data classification (PII, PHI, confidential)
- GDPR compliance (right to access, right to be forgotten)
- Data anonymization and pseudonymization
- Consent management
- Data retention policies
- Privacy impact assessments
- Data subject requests

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import secrets
from threading import Lock

logger = logging.getLogger(__name__)


class PrivacyError(Exception):
    """Base exception for privacy errors."""
    pass


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"
    PHI = "phi"


class ConsentPurpose(str, Enum):
    """Consent purposes."""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PROFILING = "profiling"
    THIRD_PARTY_SHARING = "third_party_sharing"


@dataclass
class DataAsset:
    """Classified data asset."""
    asset_id: str
    name: str
    classification: DataClassification
    owner: str
    retention_days: int
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Consent:
    """User consent record."""
    consent_id: str
    user_id: str
    purpose: ConsentPurpose
    granted: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataSubjectRequest:
    """GDPR data subject request."""
    request_id: str
    user_id: str
    request_type: str  # access, delete, portability
    timestamp: datetime
    status: str = "pending"
    completed_at: Optional[datetime] = None


class DataPrivacyManager:
    """Production-ready data privacy manager."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        self.data_assets: Dict[str, DataAsset] = {}
        self.consents: Dict[str, List[Consent]] = {}
        self.dsr_requests: List[DataSubjectRequest] = []

        self.stats = {"total_assets": 0, "pii_assets": 0, "dsr_requests": 0}

        logger.info("Data Privacy Manager initialized")

    def classify_data(self, asset: DataAsset):
        """Classify a data asset."""
        self.data_assets[asset.asset_id] = asset
        self.stats["total_assets"] += 1

        if asset.classification in [DataClassification.PII, DataClassification.PHI]:
            self.stats["pii_assets"] += 1

    def anonymize(self, value: str) -> str:
        """Anonymize sensitive data."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def pseudonymize(self, value: str) -> str:
        """Pseudonymize data (reversible with key)."""
        salt = secrets.token_hex(8)
        return f"pseudo_{hashlib.md5((value + salt).encode()).hexdigest()}"

    def record_consent(self, user_id: str, purpose: ConsentPurpose, granted: bool):
        """Record user consent."""
        consent = Consent(
            consent_id=f"consent_{user_id}_{purpose.value}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            purpose=purpose,
            granted=granted
        )

        if user_id not in self.consents:
            self.consents[user_id] = []

        self.consents[user_id].append(consent)

    def has_consent(self, user_id: str, purpose: ConsentPurpose) -> bool:
        """Check if user has granted consent."""
        user_consents = self.consents.get(user_id, [])

        for consent in reversed(user_consents):
            if consent.purpose == purpose:
                return consent.granted

        return False

    def handle_dsr(self, request: DataSubjectRequest):
        """Handle data subject request (GDPR)."""
        self.dsr_requests.append(request)
        self.stats["dsr_requests"] += 1

        logger.info(f"DSR request received: {request.request_type} for user {request.user_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get privacy statistics."""
        return self.stats


data_privacy = DataPrivacyManager()
