"""
Casbin Policy Enforcement - ITEM 23

Attribute-Based Access Control (ABAC) using Casbin.
Provides fine-grained permission checking beyond simple role checks.
"""

import os
from typing import Optional
from pathlib import Path
import casbin
from fastapi import Depends, HTTPException, status
from backend.backend.models import User, UserRole
from backend.core.security_enhanced import get_current_user
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Casbin Enforcer Initialization
# ============================================================================

def get_casbin_enforcer() -> casbin.Enforcer:
    """
    Initialize Casbin enforcer with RBAC model and policies.

    Returns:
        Configured Casbin enforcer
    """
    # Get paths to policy files
    backend_dir = Path(__file__).parent.parent
    model_path = backend_dir / "policies" / "rbac_model.conf"
    policy_path = backend_dir / "policies" / "rbac_policy.csv"

    # Check if files exist
    if not model_path.exists():
        logger.error(f"Casbin model not found: {model_path}")
        raise FileNotFoundError(f"Casbin model not found: {model_path}")

    if not policy_path.exists():
        logger.warning(f"Casbin policy not found: {policy_path}")
        # Create empty policy file if it doesn't exist
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.touch()

    # Initialize enforcer
    enforcer = casbin.Enforcer(str(model_path), str(policy_path))

    logger.info("Casbin enforcer initialized successfully")
    return enforcer


# Global enforcer instance
_enforcer: Optional[casbin.Enforcer] = None


def get_enforcer() -> casbin.Enforcer:
    """Get or create global Casbin enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = get_casbin_enforcer()
    return _enforcer


# ============================================================================
# Permission Checking
# ============================================================================

def check_permission(user: User, resource: str, action: str) -> bool:
    """
    Check if user has permission for resource and action.

    Args:
        user: User object
        resource: Resource name (e.g., 'projects', 'documents')
        action: Action name (e.g., 'read', 'create', 'update', 'delete')

    Returns:
        True if permission granted

    Examples:
        >>> check_permission(user, 'projects', 'create')
        True
        >>> check_permission(user, 'admin_panel', 'access')
        False
    """
    enforcer = get_enforcer()

    # Convert role to string
    role = user.role.value if isinstance(user.role, UserRole) else user.role

    # Check permission
    allowed = enforcer.enforce(role, resource, action)

    if not allowed:
        logger.warning(
            f"Permission denied: user={user.email}, role={role}, "
            f"resource={resource}, action={action}"
        )

    return allowed


def require_permission(resource: str, action: str):
    """
    Dependency to enforce permission checking.

    Usage:
        @app.get("/api/projects")
        async def get_projects(
            user: User = Depends(require_permission("projects", "read"))
        ):
            ...

    Args:
        resource: Resource name
        action: Action name

    Returns:
        Dependency function that checks permission
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        """Check if user has required permission."""
        if not check_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {action} {resource}"
            )
        return user

    return permission_checker


# ============================================================================
# Policy Management
# ============================================================================

def add_policy(role: str, resource: str, action: str) -> bool:
    """
    Add a new policy rule.

    Args:
        role: User role
        resource: Resource name
        action: Action name

    Returns:
        True if added successfully

    Example:
        >>> add_policy("engineer", "bim_models", "export")
        True
    """
    enforcer = get_enforcer()
    return enforcer.add_policy(role, resource, action)


def remove_policy(role: str, resource: str, action: str) -> bool:
    """
    Remove a policy rule.

    Args:
        role: User role
        resource: Resource name
        action: Action name

    Returns:
        True if removed successfully
    """
    enforcer = get_enforcer()
    return enforcer.remove_policy(role, resource, action)


def get_policies_for_role(role: str) -> list:
    """
    Get all policies for a role.

    Args:
        role: User role

    Returns:
        List of [role, resource, action] tuples

    Example:
        >>> get_policies_for_role("engineer")
        [['engineer', 'projects', 'read'], ['engineer', 'projects', 'create'], ...]
    """
    enforcer = get_enforcer()
    return enforcer.get_filtered_policy(0, role)


def get_all_policies() -> list:
    """
    Get all policy rules.

    Returns:
        List of all policies
    """
    enforcer = get_enforcer()
    return enforcer.get_policy()


# ============================================================================
# Role Management
# ============================================================================

def add_role_for_user(user_role: str, parent_role: str) -> bool:
    """
    Add role inheritance (role hierarchy).

    Args:
        user_role: Child role
        parent_role: Parent role (inherits permissions from)

    Returns:
        True if added successfully

    Example:
        >>> add_role_for_user("engineer", "operator")
        True  # Engineer inherits all Operator permissions
    """
    enforcer = get_enforcer()
    return enforcer.add_grouping_policy(user_role, parent_role)


def get_roles_for_user(user_role: str) -> list:
    """
    Get all parent roles for a user role.

    Args:
        user_role: User role

    Returns:
        List of parent roles

    Example:
        >>> get_roles_for_user("engineer")
        ['operator', 'viewer']  # Through inheritance chain
    """
    enforcer = get_enforcer()
    return enforcer.get_roles_for_user(user_role)


def get_users_for_role(role: str) -> list:
    """
    Get all child roles that inherit from this role.

    Args:
        role: Role name

    Returns:
        List of child roles

    Example:
        >>> get_users_for_role("viewer")
        ['operator', 'engineer', 'commercial', 'auditor']
    """
    enforcer = get_enforcer()
    return enforcer.get_users_for_role(role)


# ============================================================================
# Permission Queries
# ============================================================================

def get_permissions_for_user(user: User) -> dict:
    """
    Get all permissions for a user (including inherited).

    Args:
        user: User object

    Returns:
        Dictionary mapping resources to allowed actions

    Example:
        >>> get_permissions_for_user(engineer_user)
        {
            'projects': ['read', 'create', 'update'],
            'documents': ['read', 'create', 'update', 'delete'],
            ...
        }
    """
    enforcer = get_enforcer()
    role = user.role.value if isinstance(user.role, UserRole) else user.role

    # Get direct policies
    direct_policies = enforcer.get_filtered_policy(0, role)

    # Get inherited roles
    inherited_roles = enforcer.get_roles_for_user(role)

    # Collect all policies
    all_policies = direct_policies.copy()
    for parent_role in inherited_roles:
        all_policies.extend(enforcer.get_filtered_policy(0, parent_role))

    # Organize by resource
    permissions = {}
    for policy in all_policies:
        _, resource, action = policy
        if resource == "*":
            # Admin wildcard - return all permissions
            return {"*": ["*"]}

        if resource not in permissions:
            permissions[resource] = []

        if action not in permissions[resource]:
            permissions[resource].append(action)

    return permissions


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "get_enforcer",
    "check_permission",
    "require_permission",
    "add_policy",
    "remove_policy",
    "get_policies_for_role",
    "get_all_policies",
    "add_role_for_user",
    "get_roles_for_user",
    "get_users_for_role",
    "get_permissions_for_user",
]
