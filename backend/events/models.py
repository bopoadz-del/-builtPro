"""Event sourcing models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.sqlite import JSON

from backend.backend.db import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, nullable=False)
    event_type = Column(String(255), nullable=False)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow)
    workspace_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, nullable=True)
    correlation_id = Column(String(64), nullable=True)
    source = Column(String(255), nullable=False)
    payload_json = Column(JSON, nullable=False)


class WorkspaceStateProjection(Base):
    __tablename__ = "workspace_state_projection"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, unique=True, nullable=False)
    last_hydration_job_id = Column(String(255), nullable=True)
    last_hydration_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
