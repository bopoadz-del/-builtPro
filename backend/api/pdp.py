"""PDP API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.backend.db import get_db
from backend.backend.models import User, Project
from backend.backend.pdp.acl_manager import ACLManager
from backend.backend.pdp.content_scanner import ContentScanner
from backend.backend.pdp.models import AccessControlList, PDPAuditLog, Policy
from backend.backend.pdp.policy_engine import PolicyEngine
from backend.backend.pdp.rate_limiter import RateLimiter
from backend.backend.pdp.schemas import PolicyRequest, PolicyType, Role

router = APIRouter(prefix="/pdp")


@router.post("/evaluate")
def evaluate_policy(payload: Dict[str, Any], db: Session = Depends(get_db)):
    request = PolicyRequest(
        user_id=payload["user_id"],
        action=payload.get("action", "read"),
        resource_type=payload.get("resource_type", "resource"),
        resource_id=payload.get("resource_id"),
        context=payload.get("context", {}),
    )
    engine = PolicyEngine(db)
    decision = engine.evaluate(request)
    return {"allowed": decision.allowed, "reason": decision.reason}


@router.post("/access/grant", status_code=201)
def grant_access(
    user_id: int,
    project_id: int,
    role: str,
    granted_by: int,
    expires_at: str | None = None,
    db: Session = Depends(get_db),
):
    manager = ACLManager(db)
    expiry = datetime.fromisoformat(expires_at) if expires_at else None
    try:
        acl = manager.grant_access(user_id, project_id, Role(role), granted_by, expires_at=expiry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "user_id": acl.user_id,
        "project_id": acl.project_id,
        "role": acl.role,
        "permissions": acl.permissions,
        "expires_at": acl.expires_at.isoformat() if acl.expires_at else None,
    }


@router.delete("/access/revoke")
def revoke_access(user_id: int, project_id: int, db: Session = Depends(get_db)):
    manager = ACLManager(db)
    result = manager.revoke_access(user_id, project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Access not found")
    return {"message": "Access revoked"}


@router.get("/users/{user_id}/permissions")
def user_permissions(user_id: int, project_id: int | None = None, db: Session = Depends(get_db)):
    manager = ACLManager(db)
    if project_id is not None:
        return manager.get_user_permissions(user_id, project_id)
    permissions: List[str] = []
    for project in manager.list_user_projects(user_id):
        permissions.extend(project["permissions"])
    return list(set(permissions))


@router.get("/rate-limit/{user_id}/{endpoint}")
def rate_limit_status(user_id: int, endpoint: str, db: Session = Depends(get_db)):
    limiter = RateLimiter(db)
    allowed, remaining = limiter.check_limit(user_id, endpoint)
    return {
        "endpoint": endpoint,
        "limit": limiter._get_config(endpoint)["limit"],
        "remaining": remaining,
        "reset_time": limiter.get_time_until_reset(user_id, endpoint),
        "allowed": allowed,
    }


@router.post("/scan")
def scan_content(text: str, db: Session = Depends(get_db)):
    scanner = ContentScanner(db)
    result = scanner.scan(text)
    return {
        "safe": result.safe,
        "violations": result.violations,
        "severity": result.severity.value,
    }


@router.get("/audit-trail")
def audit_trail(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(PDPAuditLog).order_by(PDPAuditLog.ts.desc()).limit(limit).all()
    return [
        {
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "decision": log.decision,
            "reason": log.reason,
            "ts": log.ts.isoformat(),
        }
        for log in logs
    ]


@router.get("/policies")
def list_policies(policy_type: str | None = None, enabled: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Policy)
    if policy_type:
        query = query.filter(Policy.policy_type == policy_type)
    if enabled is not None:
        query = query.filter(Policy.enabled == (1 if enabled else 0))
    policies = query.all()
    return [
        {
            "id": policy.id,
            "name": policy.name,
            "policy_type": policy.policy_type,
            "rules": policy.rules_json,
            "enabled": bool(policy.enabled),
            "priority": policy.priority,
        }
        for policy in policies
    ]


@router.post("/policies", status_code=201)
def create_policy(payload: Dict[str, Any], db: Session = Depends(get_db)):
    policy = Policy(
        name=payload["name"],
        policy_type=payload["policy_type"],
        rules_json=payload.get("rules", {}),
        enabled=1 if payload.get("enabled", True) else 0,
        priority=payload.get("priority", 100),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return {
        "id": policy.id,
        "name": policy.name,
        "policy_type": policy.policy_type,
        "rules": policy.rules_json,
        "enabled": bool(policy.enabled),
        "priority": policy.priority,
    }


@router.put("/policies/{policy_id}")
def update_policy(policy_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.name = payload.get("name", policy.name)
    policy.policy_type = payload.get("policy_type", policy.policy_type)
    policy.rules_json = payload.get("rules", policy.rules_json)
    policy.enabled = 1 if payload.get("enabled", bool(policy.enabled)) else 0
    policy.priority = payload.get("priority", policy.priority)
    db.commit()
    return {
        "id": policy.id,
        "name": policy.name,
        "policy_type": policy.policy_type,
        "rules": policy.rules_json,
        "enabled": bool(policy.enabled),
        "priority": policy.priority,
    }


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return {"message": "Policy deleted"}
