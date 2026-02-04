"""
Authentication models for the Blank App backend.

This module defines a minimal `User` model used for dependency injection
and authentication stubs. In a production application, replace this
with a full user schema and integrate with a real authentication
system.
"""

from pydantic import BaseModel


class User(BaseModel):
    """A minimal representation of an authenticated user."""

    id: int
    username: str