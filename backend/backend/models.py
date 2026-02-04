from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func, Enum
from sqlalchemy.orm import relationship
from .db import Base


class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    ENGINEER = "engineer"
    ADMIN = "admin"
    AUDITOR = "auditor"
    SYSTEM = "system"
    USER = "user"
    DIRECTOR = "director"
    COMMERCIAL = "commercial"
    SAFETY_OFFICER = "safety_officer"
    VIEWER = "viewer"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    drive_id = Column(String, unique=True, nullable=True)  # Google Drive folder ID
    chats = relationship("Chat", back_populates="project")

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    project = relationship("Project", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    liked = Column(Boolean, default=False)
    disliked = Column(Boolean, default=False)
    copied = Column(Boolean, default=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat = relationship("Chat", back_populates="messages")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Integer, default=0)

    user = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())