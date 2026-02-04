"""
Security utilities and dependency stubs for the Blank App backend.

This module defines a `get_current_user` dependency used by API
endpoints. It currently returns a hardcoded user for demonstration
purposes. In a production environment, replace this with proper
authentication and authorization logic (e.g., JWT token
verification, OAuth). The function is implemented as a regular
callable rather than a dependency class to simplify integration.
"""

from typing import Any
from fastapi import Depends, HTTPException, status

from backend.models.auth import User


def get_current_user() -> User:
    """
    Dependency that returns the current authenticated user.

    Returns:
        A `User` instance representing the authenticated user.

    Raises:
        HTTPException: If authentication fails. In this stub
        implementation, authentication always succeeds and returns a
        dummy user.
    """
    # In a real application, this would verify a token or session.
    # Here we return a dummy user with id=1 and username="demo".
    return User(id=1, username="demo")