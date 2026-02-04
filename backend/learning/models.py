"""Learning feedback models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from backend.backend.db import Base


class Feedback(Base):
    __tablename__ = "learning_feedback"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False)
    user_id = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)
    input_text = Column(String, nullable=False)
    output_text = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    labels = relationship("FeedbackLabel", back_populates="feedback", cascade="all, delete-orphan")
    reviews = relationship("FeedbackReview", back_populates="feedback", cascade="all, delete-orphan")


class FeedbackLabel(Base):
    __tablename__ = "learning_feedback_labels"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("learning_feedback.id"), nullable=False)
    label_type = Column(String(50), nullable=False)
    label_data_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    feedback = relationship("Feedback", back_populates="labels")


class FeedbackReview(Base):
    __tablename__ = "learning_feedback_reviews"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("learning_feedback.id"), nullable=False)
    reviewer_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    feedback = relationship("Feedback", back_populates="reviews")
