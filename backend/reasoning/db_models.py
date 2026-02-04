"""Reasoning layer database models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.backend.db import Base


class DocumentEntity(Base):
    __tablename__ = "reasoning_document_entities"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False)
    document_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DocumentLink(Base):
    __tablename__ = "reasoning_document_links"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)
    entity_id = Column(Integer, nullable=False)
    link_type = Column(String(50), nullable=False, default="mentions")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
