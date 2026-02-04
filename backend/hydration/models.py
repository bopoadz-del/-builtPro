"""Hydration models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from backend.backend.db import Base


class SourceType(str, Enum):
    GOOGLE_DRIVE = "google_drive"
    SERVER_FS = "server_fs"


class WorkspaceSource(Base):
    __tablename__ = "workspace_sources"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    config_json = Column(String, nullable=False)
    cursor_json = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    source_document_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    checksum = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="versions")


class HydrationRun(Base):
    __tablename__ = "hydration_runs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    files_seen = Column(Integer, default=0)
    status = Column(String(50), default="running")


class HydrationRunItem(Base):
    __tablename__ = "hydration_run_items"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("hydration_runs.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("workspace_sources.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(50), default="processed")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
