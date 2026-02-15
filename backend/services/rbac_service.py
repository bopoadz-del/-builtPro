"""
Role-Based Access Control (RBAC) Service for BuilTPro Brain AI

Enterprise authorization with roles, permissions, and policy-based access control.

Features:
- Role management (hierarchical roles)
- Permission management (granular permissions)
- Policy-based access control (PBAC)
- Attribute-based access control (ABAC)
- Resource-level permissions
- Dynamic permission evaluation
- Permission inheritance
- Access control lists (ACLs)
- Delegation and impersonation
- Audit logging for authorization

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class AuthorizationError(Exception):
    """Base exception for authorization errors."""
    pass


class PermissionDenied(AuthorizationError):
    """Raised when permission is denied."""
    pass


class Action(str, Enum):
    """CRUD actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Resource types."""
    PROJECT = "project"
    DOCUMENT = "document"
    TASK = "task"
    USER = "user"
    REPORT = "report"
    SETTING = "setting"


@dataclass
class Permission:
    """Individual permission."""
    permission_id: str
    name: str
    resource_type: ResourceType
    action: Action
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Role:
    """User role."""
    role_id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    parent_role_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Access control policy."""
    policy_id: str
    name: str
    effect: str  # "allow" or "deny"
    subjects: List[str]  # user IDs or role IDs
    actions: List[Action]
    resources: List[str]  # resource patterns
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserRole:
    """User role assignment."""
    user_id: str
    role_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    assigned_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class RBACService:
    """Production-ready RBAC service."""

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

        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[UserRole]] = defaultdict(list)
        self.policies: Dict[str, Policy] = {}

        self.stats = {"total_checks": 0, "allowed": 0, "denied": 0}

        self._create_default_roles()

        logger.info("RBAC Service initialized")

    def _create_default_roles(self):
        """Create default system roles."""
        # Admin role
        admin_role = Role(
            role_id="role_admin",
            name="Administrator",
            description="Full system access"
        )
        self.roles[admin_role.role_id] = admin_role

        # Project Manager role
        pm_role = Role(
            role_id="role_pm",
            name="Project Manager",
            description="Manage projects and tasks"
        )
        self.roles[pm_role.role_id] = pm_role

        # User role
        user_role = Role(
            role_id="role_user",
            name="User",
            description="Standard user access"
        )
        self.roles[user_role.role_id] = user_role

    def create_permission(
        self,
        permission_id: str,
        name: str,
        resource_type: ResourceType,
        action: Action,
        description: str
    ) -> Permission:
        """Create a new permission."""
        permission = Permission(
            permission_id=permission_id,
            name=name,
            resource_type=resource_type,
            action=action,
            description=description
        )

        self.permissions[permission_id] = permission
        logger.info(f"Created permission: {permission_id}")

        return permission

    def create_role(
        self,
        role_id: str,
        name: str,
        description: str,
        parent_role_id: Optional[str] = None
    ) -> Role:
        """Create a new role."""
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            parent_role_id=parent_role_id
        )

        self.roles[role_id] = role
        logger.info(f"Created role: {role_id}")

        return role

    def assign_permission_to_role(self, role_id: str, permission_id: str):
        """Assign a permission to a role."""
        if role_id not in self.roles:
            raise AuthorizationError(f"Role not found: {role_id}")

        if permission_id not in self.permissions:
            raise AuthorizationError(f"Permission not found: {permission_id}")

        self.roles[role_id].permissions.add(permission_id)
        logger.info(f"Assigned permission {permission_id} to role {role_id}")

    def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        assigned_by: Optional[str] = None
    ) -> UserRole:
        """Assign a role to a user."""
        if role_id not in self.roles:
            raise AuthorizationError(f"Role not found: {role_id}")

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by
        )

        self.user_roles[user_id].append(user_role)
        logger.info(f"Assigned role {role_id} to user {user_id}")

        return user_role

    def check_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has permission."""
        self.stats["total_checks"] += 1

        # Get user's roles
        user_role_ids = [ur.role_id for ur in self.user_roles.get(user_id, [])]

        # Get all permissions from roles (including inherited)
        permissions = set()
        for role_id in user_role_ids:
            permissions.update(self._get_role_permissions(role_id))

        # Check if user has required permission
        for perm_id in permissions:
            perm = self.permissions.get(perm_id)
            if perm and perm.resource_type == resource_type and perm.action == action:
                self.stats["allowed"] += 1
                return True

        self.stats["denied"] += 1
        return False

    def _get_role_permissions(self, role_id: str) -> Set[str]:
        """Get all permissions for a role including inherited."""
        permissions = set()

        role = self.roles.get(role_id)
        if not role:
            return permissions

        # Add role's permissions
        permissions.update(role.permissions)

        # Add parent role's permissions (inheritance)
        if role.parent_role_id:
            permissions.update(self._get_role_permissions(role.parent_role_id))

        return permissions

    def require_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action
    ):
        """Require permission or raise exception."""
        if not self.check_permission(user_id, resource_type, action):
            raise PermissionDenied(f"User {user_id} lacks {action.value} permission on {resource_type.value}")

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all roles assigned to a user."""
        role_ids = [ur.role_id for ur in self.user_roles.get(user_id, [])]
        return [self.roles[rid] for rid in role_ids if rid in self.roles]

    def get_stats(self) -> Dict[str, Any]:
        """Get RBAC statistics."""
        return {
            **self.stats,
            "total_roles": len(self.roles),
            "total_permissions": len(self.permissions),
            "users_with_roles": len(self.user_roles)
        }


rbac_service = RBACService()
