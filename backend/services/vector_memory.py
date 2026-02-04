"""Vector memory helpers for chat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ActiveProject:
    id: str
    collection: Any | None = None


_active_project: ActiveProject | None = None


def set_active_project(project: Any | None = None) -> None:
    global _active_project
    if project is None:
        _active_project = None
    elif isinstance(project, ActiveProject):
        _active_project = project
    elif isinstance(project, dict):
        _active_project = ActiveProject(id=project.get("id"), collection=project.get("collection"))
    else:
        _active_project = ActiveProject(id=str(project))


def get_active_project() -> Optional[ActiveProject]:
    return _active_project
