"""Policy engine for PDP decisions."""

from __future__ import annotations

from typing import List

from .acl_manager import ACLManager
from .content_scanner import ContentScanner
from .models import PDPAuditLog, Policy
from .rate_limiter import RateLimiter
from .rules import ContentProhibitionRule, DataClassificationRule, ProjectAccessRule, RoleBasedRule
from .schemas import PolicyDecision, PolicyRequest


class PolicyEngine:
    def __init__(self, db_session) -> None:
        self.db_session = db_session
        self.rate_limiter = RateLimiter(db_session)
        self.content_scanner = ContentScanner(db_session)
        self.acl_manager = ACLManager(db_session)
        self.policies: List[Policy] = []
        self.load_policies()

    def load_policies(self) -> None:
        self.policies = (
            self.db_session.query(Policy)
            .filter(Policy.enabled == 1)
            .order_by(Policy.priority.desc())
            .all()
        )

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        decision = self.apply_policy_chain(request)
        self._log_decision(request, decision)
        return decision

    def check_access(self, request: PolicyRequest) -> PolicyDecision:
        role_rule = RoleBasedRule()
        allowed, reason = role_rule.evaluate(request, self.db_session)
        if not allowed:
            return PolicyDecision(allowed=False, reason=reason)

        project_rule = ProjectAccessRule()
        allowed, reason = project_rule.evaluate(request, self.db_session)
        if not allowed:
            return PolicyDecision(allowed=False, reason=reason)
        return PolicyDecision(allowed=True, reason="Access allowed")

    def check_rate_limit(self, request: PolicyRequest) -> PolicyDecision:
        endpoint = request.context.get("endpoint") if request.context else None
        if not endpoint:
            endpoint = request.resource_type or "default"
        allowed, _ = self.rate_limiter.check_limit(request.user_id, endpoint)
        if not allowed:
            return PolicyDecision(allowed=False, reason="Rate limit exceeded")
        self.rate_limiter.increment(request.user_id, endpoint)
        return PolicyDecision(allowed=True, reason="Rate limit ok")

    def check_content(self, request: PolicyRequest) -> PolicyDecision:
        content = request.context.get("content") if request.context else None
        if not content:
            return PolicyDecision(allowed=True, reason="No content to scan")
        rule = ContentProhibitionRule()
        allowed, reason = rule.evaluate(request, self.db_session)
        if allowed:
            return PolicyDecision(allowed=True, reason=reason)
        return PolicyDecision(allowed=False, reason=f"Violation: {reason}")

    def check_classification(self, request: PolicyRequest) -> PolicyDecision:
        rule = DataClassificationRule()
        allowed, reason = rule.evaluate(request, self.db_session)
        return PolicyDecision(allowed=allowed, reason=reason)

    def apply_policy_chain(self, request: PolicyRequest) -> PolicyDecision:
        decision = self.check_access(request)
        decision.conditions.append("access")
        if not decision.allowed:
            return decision

        rate_decision = self.check_rate_limit(request)
        decision.conditions.append("rate_limit")
        if not rate_decision.allowed:
            return rate_decision

        content_decision = self.check_content(request)
        decision.conditions.append("content")
        if not content_decision.allowed:
            return content_decision

        classification_decision = self.check_classification(request)
        decision.conditions.append("classification")
        if not classification_decision.allowed:
            return classification_decision

        return PolicyDecision(allowed=True, reason="All checks passed", conditions=decision.conditions)

    def _log_decision(self, request: PolicyRequest, decision: PolicyDecision) -> None:
        audit = PDPAuditLog(
            user_id=request.user_id,
            action=request.action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            decision="allow" if decision.allowed else "deny",
            reason=decision.reason,
        )
        self.db_session.add(audit)
        self.db_session.commit()
