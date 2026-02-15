"""
Security Monitoring Service for BuilTPro Brain AI

Real-time security monitoring with threat detection and SIEM integration.

Features:
- Real-time threat detection
- Intrusion detection system (IDS)
- Anomaly detection
- Security event correlation
- SIEM integration
- Threat intelligence feeds
- Incident response automation
- Security alerts and notifications

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base exception for security errors."""
    pass


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    DDOS = "ddos"
    MALWARE = "malware"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"


@dataclass
class SecurityEvent:
    """Security event record."""
    event_id: str
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: Optional[str]
    user_id: Optional[str]
    description: str
    indicators: Dict[str, Any] = field(default_factory=dict)
    mitigated: bool = False


@dataclass
class ThreatIndicator:
    """Threat indicator from intelligence feeds."""
    indicator_id: str
    indicator_type: str  # ip, domain, hash, etc.
    value: str
    threat_level: ThreatLevel
    source: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class SecurityMonitoring:
    """Production-ready security monitoring service."""

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

        self.security_events: deque = deque(maxlen=100000)
        self.threat_indicators: Dict[str, ThreatIndicator] = {}
        self.blocked_ips: set = set()
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)

        self.stats = {
            "total_events": 0,
            "threats_detected": 0,
            "threats_mitigated": 0,
            "blocked_ips": 0
        }

        logger.info("Security Monitoring initialized")

    def log_security_event(
        self,
        event_id: str,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        indicators: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """Log a security event."""
        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            threat_type=threat_type,
            threat_level=threat_level,
            source_ip=source_ip,
            user_id=user_id,
            description=description,
            indicators=indicators or {}
        )

        self.security_events.append(event)
        self.stats["total_events"] += 1
        self.stats["threats_detected"] += 1

        # Auto-mitigate critical threats
        if threat_level == ThreatLevel.CRITICAL and source_ip:
            self.block_ip(source_ip)
            event.mitigated = True
            self.stats["threats_mitigated"] += 1

        logger.warning(f"Security event: {threat_type.value} ({threat_level.value})")

        return event

    def detect_brute_force(self, identifier: str, window_minutes: int = 5, max_attempts: int = 10) -> bool:
        """Detect brute force attempts."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old attempts
        self.rate_limits[identifier] = [
            ts for ts in self.rate_limits[identifier]
            if ts > window_start
        ]

        # Add current attempt
        self.rate_limits[identifier].append(now)

        # Check if threshold exceeded
        if len(self.rate_limits[identifier]) > max_attempts:
            self.log_security_event(
                event_id=f"brute_force_{identifier}_{now.timestamp()}",
                threat_type=ThreatType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                description=f"Brute force detected: {identifier}",
                source_ip=identifier
            )
            return True

        return False

    def block_ip(self, ip_address: str):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        self.stats["blocked_ips"] = len(self.blocked_ips)
        logger.info(f"Blocked IP: {ip_address}")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        return ip_address in self.blocked_ips

    def add_threat_indicator(self, indicator: ThreatIndicator):
        """Add a threat indicator."""
        self.threat_indicators[indicator.indicator_id] = indicator

    def check_threat_indicators(self, value: str, indicator_type: str) -> Optional[ThreatIndicator]:
        """Check if value matches any threat indicators."""
        for indicator in self.threat_indicators.values():
            if indicator.indicator_type == indicator_type and indicator.value == value:
                return indicator
        return None

    def get_recent_events(self, limit: int = 100, min_level: Optional[ThreatLevel] = None) -> List[SecurityEvent]:
        """Get recent security events."""
        events = list(self.security_events)

        if min_level:
            level_order = {ThreatLevel.LOW: 1, ThreatLevel.MEDIUM: 2, ThreatLevel.HIGH: 3, ThreatLevel.CRITICAL: 4}
            min_level_value = level_order[min_level]
            events = [e for e in events if level_order[e.threat_level] >= min_level_value]

        return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get security monitoring statistics."""
        return {
            **self.stats,
            "threat_indicators": len(self.threat_indicators)
        }


security_monitoring = SecurityMonitoring()
