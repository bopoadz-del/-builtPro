"""
Pydantic schemas for request and response models.

This package aggregates Pydantic models used across the API for
input validation and output serialization.  Grouping schemas in a
dedicated package helps enforce consistent validation rules and
reduces coupling between endpoints and underlying models.
"""

from .users import UserRegister, UserLogin

__all__ = [
    "UserRegister",
    "UserLogin",
]