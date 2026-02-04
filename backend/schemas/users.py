"""
User schemas for request validation.

Defines Pydantic models representing the payloads for user
registration and login.  These are re-exported via
``app.schemas.__init__`` for convenience.
"""

from pydantic import BaseModel, constr


class UserRegister(BaseModel):
    """Schema for user registration requests."""

    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(min_length=6, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login requests."""

    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(min_length=6, max_length=128)