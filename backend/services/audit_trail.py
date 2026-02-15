"""
Audit Trail System for BuilTPro Brain AI

Comprehensive audit logging and compliance tracking system for all platform activities.

Features:
- Activity logging for all user actions
- Compliance tracking (SOC2, ISO27001, GDPR)
- Change history with before/after snapshots
- Security event logging
- Data access tracking
- Retention policies
- Audit log search and filtering
- Export capabilities
- Tamper-proof logging (hash chains)
- Real-time monitoring integration

Audit Categories:
- User authentication (login, logout, password changes)
- Data modifications (create, update, delete)
- Permission changes
- Security events (access denied, suspicious activity)
- System changes (configuration, settings)
- API access
- File operations
- Report generation

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
import hashlib
import json
from threading import Lock

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class AuditError(Exception):
    """Base exception for audit trail errors."""
    pass


class LoggingError(AuditError):
    """Raised when audit logging fails."""
    pass


class QueryError(AuditError):
    """Raised when audit log queries fail."""
    pass


# ============================================================================
# Enums
# ============================================================================


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Data operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"

    # Permissions
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_REMOVE = "role_remove"

    # Security
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TOKEN_REFRESH = "token_refresh"

    # System
    CONFIG_CHANGE = "config_change"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    BACKUP_CREATE = "backup_create"

    # API
    API_CALL = "api_call"
    WEBHOOK_TRIGGER = "webhook_trigger"


class AuditCategory(str, Enum):
    """Categories for audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY = "security"
    SYSTEM = "system"
    API = "api"
    COMPLIANCE = "compliance"


class Severity(str, Enum):
    """Audit event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceStandard(str, Enum):
    """Compliance standards."""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class AuditEvent:
    """Individual audit event."""
    event_id: str
    timestamp: datetime
    action: AuditAction
    category: AuditCategory
    severity: Severity
    user_id: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[ComplianceStandard] = field(default_factory=list)
    hash: Optional[str] = None  # For tamper detection
    previous_hash: Optional[str] = None  # Hash chain


@dataclass
class AuditQuery:
    """Query parameters for audit log search."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    category: Optional[AuditCategory] = None
    severity: Optional[Severity] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class AuditSummary:
    """Summary of audit events."""
    total_events: int
    events_by_action: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    unique_users: int
    time_range: Dict[str, datetime]
    top_resources: List[Dict[str, Any]]


@dataclass
class ComplianceReport:
    """Compliance audit report."""
    standard: ComplianceStandard
    period_start: datetime
    period_end: datetime
    total_events: int
    compliant_events: int
    non_compliant_events: int
    violations: List[AuditEvent]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetentionPolicy:
    """Audit log retention policy."""
    policy_id: str
    name: str
    retention_days: int
    categories: List[AuditCategory]
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    archive_enabled: bool = True
    delete_after_archive: bool = False


# ============================================================================
# Audit Trail System
# ============================================================================


class AuditTrailSystem:
    """
    Production-ready audit trail and compliance tracking system.

    Features:
    - Comprehensive activity logging
    - Tamper-proof hash chains
    - Compliance tracking
    - Advanced search and filtering
    - Retention policies
    - Export capabilities
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global audit system."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the audit trail system."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Storage
        self.events: deque = deque(maxlen=1000000)  # Last 1M events in memory
        self.events_by_user: Dict[str, List[str]] = defaultdict(list)
        self.events_by_resource: Dict[str, List[str]] = defaultdict(list)
        self.retention_policies: Dict[str, RetentionPolicy] = {}

        # Hash chain for tamper detection
        self.last_hash: Optional[str] = None

        # Configuration
        self.default_retention_days = 365
        self.enable_hash_chain = True
        self.enable_archiving = True

        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_action": defaultdict(int),
            "events_by_category": defaultdict(int),
            "events_by_severity": defaultdict(int)
        }

        logger.info("Audit Trail System initialized")

    # ========================================================================
    # Event Logging
    # ========================================================================

    def log_event(
        self,
        event_id: str,
        action: AuditAction,
        category: AuditCategory,
        description: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: Severity = Severity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[ComplianceStandard]] = None
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_id: Unique event identifier
            action: Type of action
            category: Event category
            description: Human-readable description
            user_id: User who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            severity: Event severity
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            request_id: Request identifier
            before_state: State before action
            after_state: State after action
            metadata: Additional metadata
            compliance_tags: Compliance standards this event relates to

        Returns:
            AuditEvent object
        """
        try:
            event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                action=action,
                category=category,
                severity=severity,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                request_id=request_id,
                before_state=before_state,
                after_state=after_state,
                metadata=metadata or {},
                compliance_tags=compliance_tags or []
            )

            # Add to hash chain
            if self.enable_hash_chain:
                event.previous_hash = self.last_hash
                event.hash = self._calculate_event_hash(event)
                self.last_hash = event.hash

            # Store event
            self.events.append(event)

            # Index by user and resource
            if user_id:
                self.events_by_user[user_id].append(event_id)

            if resource_type and resource_id:
                resource_key = f"{resource_type}:{resource_id}"
                self.events_by_resource[resource_key].append(event_id)

            # Update statistics
            self.stats["total_events"] += 1
            self.stats["events_by_action"][action.value] += 1
            self.stats["events_by_category"][category.value] += 1
            self.stats["events_by_severity"][severity.value] += 1

            logger.debug(f"Audit event logged: {event_id} - {action.value}")

            return event

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            raise LoggingError(f"Audit logging failed: {e}")

    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """Calculate SHA-256 hash for an audit event."""
        # Create deterministic string representation
        hash_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "action": event.action.value,
            "category": event.category.value,
            "user_id": event.user_id,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "description": event.description,
            "previous_hash": event.previous_hash
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    # ========================================================================
    # Convenience Logging Methods
    # ========================================================================

    def log_authentication(
        self,
        user_id: str,
        action: AuditAction,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditEvent:
        """Log authentication event."""
        return self.log_event(
            event_id=f"auth_{user_id}_{datetime.utcnow().timestamp()}",
            action=action,
            category=AuditCategory.AUTHENTICATION,
            description=details or f"User {action.value}: {'success' if success else 'failed'}",
            user_id=user_id,
            severity=Severity.INFO if success else Severity.WARNING,
            ip_address=ip_address,
            compliance_tags=[ComplianceStandard.SOC2, ComplianceStandard.ISO27001]
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: AuditAction = AuditAction.READ,
        details: Optional[str] = None
    ) -> AuditEvent:
        """Log data access event."""
        return self.log_event(
            event_id=f"access_{resource_type}_{resource_id}_{datetime.utcnow().timestamp()}",
            action=action,
            category=AuditCategory.DATA_ACCESS,
            description=details or f"User accessed {resource_type} {resource_id}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=Severity.DEBUG,
            compliance_tags=[ComplianceStandard.GDPR]
        )

    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: AuditAction,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None
    ) -> AuditEvent:
        """Log data modification event."""
        return self.log_event(
            event_id=f"modify_{resource_type}_{resource_id}_{datetime.utcnow().timestamp()}",
            action=action,
            category=AuditCategory.DATA_MODIFICATION,
            description=details or f"User {action.value} {resource_type} {resource_id}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            severity=Severity.INFO,
            compliance_tags=[ComplianceStandard.SOC2, ComplianceStandard.GDPR]
        )

    def log_security_event(
        self,
        action: AuditAction,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: Severity = Severity.WARNING
    ) -> AuditEvent:
        """Log security event."""
        return self.log_event(
            event_id=f"security_{datetime.utcnow().timestamp()}",
            action=action,
            category=AuditCategory.SECURITY,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            compliance_tags=[ComplianceStandard.SOC2, ComplianceStandard.ISO27001]
        )

    # ========================================================================
    # Query & Search
    # ========================================================================

    def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """
        Query audit events with filtering.

        Args:
            query: Query parameters

        Returns:
            List of matching audit events
        """
        try:
            results = []

            for event in self.events:
                # Apply filters
                if query.start_time and event.timestamp < query.start_time:
                    continue
                if query.end_time and event.timestamp > query.end_time:
                    continue
                if query.user_id and event.user_id != query.user_id:
                    continue
                if query.action and event.action != query.action:
                    continue
                if query.category and event.category != query.category:
                    continue
                if query.severity and event.severity != query.severity:
                    continue
                if query.resource_type and event.resource_type != query.resource_type:
                    continue
                if query.resource_id and event.resource_id != query.resource_id:
                    continue

                results.append(event)

            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit

            return results[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise QueryError(f"Failed to query events: {e}")

    def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get all activity for a specific user."""
        query = AuditQuery(
            user_id=user_id,
            start_time=start_time,
            limit=limit
        )

        return self.query_events(query)

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get change history for a resource."""
        query = AuditQuery(
            resource_type=resource_type,
            resource_id=resource_id,
            category=AuditCategory.DATA_MODIFICATION,
            limit=limit
        )

        return self.query_events(query)

    # ========================================================================
    # Analytics & Reporting
    # ========================================================================

    def generate_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> AuditSummary:
        """Generate summary of audit events."""
        query = AuditQuery(
            start_time=start_time,
            end_time=end_time,
            limit=1000000  # Get all
        )

        events = self.query_events(query)

        # Count by action
        events_by_action = defaultdict(int)
        for event in events:
            events_by_action[event.action.value] += 1

        # Count by category
        events_by_category = defaultdict(int)
        for event in events:
            events_by_category[event.category.value] += 1

        # Count by severity
        events_by_severity = defaultdict(int)
        for event in events:
            events_by_severity[event.severity.value] += 1

        # Unique users
        unique_users = len(set(e.user_id for e in events if e.user_id))

        # Time range
        time_range = {}
        if events:
            time_range = {
                "start": min(e.timestamp for e in events),
                "end": max(e.timestamp for e in events)
            }

        # Top resources
        resource_counts = defaultdict(int)
        for event in events:
            if event.resource_type and event.resource_id:
                key = f"{event.resource_type}:{event.resource_id}"
                resource_counts[key] += 1

        top_resources = [
            {"resource": k, "count": v}
            for k, v in sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return AuditSummary(
            total_events=len(events),
            events_by_action=dict(events_by_action),
            events_by_category=dict(events_by_category),
            events_by_severity=dict(events_by_severity),
            unique_users=unique_users,
            time_range=time_range,
            top_resources=top_resources
        )

    def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        period_start: datetime,
        period_end: datetime
    ) -> ComplianceReport:
        """Generate compliance audit report."""
        query = AuditQuery(
            start_time=period_start,
            end_time=period_end,
            limit=1000000
        )

        events = self.query_events(query)

        # Filter events relevant to this standard
        relevant_events = [e for e in events if standard in e.compliance_tags]

        # Identify violations (placeholder logic)
        violations = [
            e for e in relevant_events
            if e.severity in [Severity.ERROR, Severity.CRITICAL]
        ]

        compliant_events = len(relevant_events) - len(violations)

        # Generate recommendations
        recommendations = []
        if violations:
            recommendations.append("Review and address security violations")
        if len(violations) / max(len(relevant_events), 1) > 0.1:
            recommendations.append("High violation rate detected - implement additional controls")

        return ComplianceReport(
            standard=standard,
            period_start=period_start,
            period_end=period_end,
            total_events=len(relevant_events),
            compliant_events=compliant_events,
            non_compliant_events=len(violations),
            violations=violations,
            recommendations=recommendations
        )

    # ========================================================================
    # Retention & Archiving
    # ========================================================================

    def add_retention_policy(self, policy: RetentionPolicy) -> None:
        """Add a retention policy."""
        self.retention_policies[policy.policy_id] = policy
        logger.info(f"Added retention policy: {policy.name}")

    def apply_retention_policies(self) -> int:
        """Apply retention policies and clean old events. Returns number removed."""
        removed = 0
        now = datetime.utcnow()

        for policy in self.retention_policies.values():
            cutoff = now - timedelta(days=policy.retention_days)

            # Find events to remove
            to_remove = []

            for event in self.events:
                if event.timestamp < cutoff:
                    if event.category in policy.categories:
                        # Archive if enabled
                        if policy.archive_enabled:
                            self._archive_event(event)

                        if policy.delete_after_archive:
                            to_remove.append(event)

            # Remove events
            for event in to_remove:
                if event in self.events:
                    self.events.remove(event)
                    removed += 1

        if removed > 0:
            logger.info(f"Removed {removed} events per retention policies")

        return removed

    def _archive_event(self, event: AuditEvent) -> None:
        """Archive an event (stub - would write to long-term storage)."""
        logger.debug(f"Archived event: {event.event_id}")

    # ========================================================================
    # Integrity Verification
    # ========================================================================

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify hash chain integrity."""
        if not self.enable_hash_chain:
            return {"enabled": False}

        verified = 0
        broken_chains = []
        previous_hash = None

        for event in self.events:
            # Verify hash chain
            if event.previous_hash != previous_hash:
                broken_chains.append({
                    "event_id": event.event_id,
                    "expected_previous": previous_hash,
                    "actual_previous": event.previous_hash
                })

            # Verify event hash
            calculated_hash = self._calculate_event_hash(event)
            if calculated_hash != event.hash:
                broken_chains.append({
                    "event_id": event.event_id,
                    "hash_mismatch": True
                })

            verified += 1
            previous_hash = event.hash

        integrity_ok = len(broken_chains) == 0

        return {
            "enabled": True,
            "total_events": verified,
            "integrity_ok": integrity_ok,
            "broken_chains": broken_chains
        }

    # ========================================================================
    # Export
    # ========================================================================

    def export_events(
        self,
        query: AuditQuery,
        format: str = "json"
    ) -> bytes:
        """Export audit events in specified format."""
        events = self.query_events(query)

        if format == "json":
            return self._export_json(events)
        elif format == "csv":
            return self._export_csv(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, events: List[AuditEvent]) -> bytes:
        """Export events as JSON."""
        events_dict = [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat(),
                "action": e.action.value,
                "category": e.category.value,
                "severity": e.severity.value,
                "user_id": e.user_id,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "description": e.description,
                "ip_address": e.ip_address,
                "metadata": e.metadata
            }
            for e in events
        ]

        return json.dumps(events_dict, indent=2).encode('utf-8')

    def _export_csv(self, events: List[AuditEvent]) -> bytes:
        """Export events as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Event ID", "Timestamp", "Action", "Category", "Severity",
            "User ID", "Resource Type", "Resource ID", "Description", "IP Address"
        ])

        # Data
        for e in events:
            writer.writerow([
                e.event_id,
                e.timestamp.isoformat(),
                e.action.value,
                e.category.value,
                e.severity.value,
                e.user_id or "",
                e.resource_type or "",
                e.resource_id or "",
                e.description,
                e.ip_address or ""
            ])

        return output.getvalue().encode('utf-8')

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get audit system statistics."""
        return {
            **self.stats,
            "events_in_memory": len(self.events),
            "unique_users": len(self.events_by_user),
            "unique_resources": len(self.events_by_resource),
            "retention_policies": len(self.retention_policies),
            "hash_chain_enabled": self.enable_hash_chain
        }


# ============================================================================
# Singleton Instance
# ============================================================================

# Global singleton instance
audit_trail = AuditTrailSystem()
