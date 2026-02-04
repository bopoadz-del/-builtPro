"""Access control list management."""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import and_

from ..models import Project, User
from .models import AccessControlList
from .schemas import Role

ROLE_PERMISSIONS = {
    Role.ADMIN: ["admin", "read", "write", "execute", "delete", "export"],
    Role.DIRECTOR: ["read", "write", "execute", "export"],
    Role.ENGINEER: ["read", "write", "execute"],
    Role.VIEWER: ["read"],
}


class ACLManager:
    def __init__(self, db_session) -> None:
        self.db_session = db_session

    def grant_access(
        self,
        user_id: int,
        project_id: int,
        role: Role,
        granted_by: int,
        expires_at: datetime | None = None,
    ) -> AccessControlList:
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("User not found")
        project = self.db_session.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise ValueError("Project not found")

        acl = (
            self.db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None:
            acl = AccessControlList(user_id=user_id, project_id=project_id, role=role.value)
            self.db_session.add(acl)
        acl.role = role.value
        acl.permissions_json = ROLE_PERMISSIONS[role]
        acl.granted_by = granted_by
        acl.granted_at = datetime.utcnow()
        acl.expires_at = expires_at
        self.db_session.commit()
        return acl

    def revoke_access(self, user_id: int, project_id: int) -> bool:
        acl = (
            self.db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None:
            return False
        self.db_session.delete(acl)
        self.db_session.commit()
        return True

    def _is_expired(self, acl: AccessControlList) -> bool:
        return acl.expires_at is not None and acl.expires_at < datetime.utcnow()

    def check_permission(self, user_id: int, project_id: int, permission: str) -> bool:
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if user and user.role == Role.ADMIN.value:
            return True

        acl = (
            self.db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None:
            return False
        if self._is_expired(acl):
            return False
        if acl.role == Role.ADMIN.value:
            return True
        return permission in acl.permissions

    def list_user_projects(self, user_id: int) -> List[dict]:
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if user and user.role == Role.ADMIN.value:
            projects = self.db_session.query(Project).all()
            return [
                {
                    "project_id": project.id,
                    "role": Role.ADMIN.value,
                    "permissions": ROLE_PERMISSIONS[Role.ADMIN],
                }
                for project in projects
            ]

        acls = self.db_session.query(AccessControlList).filter(AccessControlList.user_id == user_id).all()
        results: List[dict] = []
        for acl in acls:
            if self._is_expired(acl):
                continue
            results.append(
                {
                    "project_id": acl.project_id,
                    "role": acl.role,
                    "permissions": acl.permissions,
                }
            )
        return results

    def get_user_permissions(self, user_id: int, project_id: int) -> List[str]:
        if self.check_permission(user_id, project_id, "admin"):
            return ROLE_PERMISSIONS[Role.ADMIN]
        acl = (
            self.db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None or self._is_expired(acl):
            return []
        return acl.permissions

    def update_permissions(self, user_id: int, project_id: int, permissions: List[str]) -> AccessControlList | None:
        acl = (
            self.db_session.query(AccessControlList)
            .filter(and_(AccessControlList.user_id == user_id, AccessControlList.project_id == project_id))
            .first()
        )
        if acl is None:
            return None
        acl.permissions_json = permissions
        self.db_session.commit()
        return acl

    def list_project_users(self, project_id: int) -> List[dict]:
        users: List[dict] = []
        acls = self.db_session.query(AccessControlList).filter(AccessControlList.project_id == project_id).all()
        for acl in acls:
            if self._is_expired(acl):
                continue
            users.append(
                {
                    "user_id": acl.user_id,
                    "permissions": acl.permissions,
                }
            )
        admin_users = self.db_session.query(User).filter(User.role == Role.ADMIN.value).all()
        for admin in admin_users:
            users.append({"user_id": admin.id, "permissions": ROLE_PERMISSIONS[Role.ADMIN]})
        return users
