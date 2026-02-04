"""
Authentication routes for the Blank App.

This module defines simple login and registration endpoints.  In a
production application you would integrate with a proper user model
stored in a database, use secure password hashing and issue JWT
tokens.  The implementation here is deliberately minimal and should
be replaced in real deployments.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext

# In-memory user store for demonstration purposes.  Keys are
# usernames and values are dicts with a hashed password.  Replace
# this with real persistence (e.g. a database) in production.
_users_db: dict[str, dict[str, str]] = {}

router = APIRouter()

# Password hashing context.  Bcrypt is a widely used algorithm.  In
# production you should configure the parameters appropriately.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegister(BaseModel):
    """Schema for user registration requests."""

    username: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login requests."""

    username: str
    password: str


@router.post("/register", summary="Register a new user")
async def register_user(payload: UserRegister) -> dict[str, str]:
    """Register a new user.

    This endpoint hashes the provided password and stores the
    credentials in an in-memory store.  It rejects duplicate
    usernames.  In production, you would write to a user table
    instead of a dictionary and return a more detailed response.
    """
    username = payload.username.strip().lower()
    if not username or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )
    if username in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    # Hash the password before storing it
    hashed = pwd_context.hash(payload.password)
    _users_db[username] = {"hashed_password": hashed}
    return {"message": "User registered successfully"}


@router.post("/login", summary="Authenticate a user and return a token")
async def login_user(payload: UserLogin) -> dict[str, str]:
    """Authenticate a user.

    This endpoint verifies that a user exists and that the supplied
    password matches the stored hash.  On success it returns a
    placeholder access token.  In a real application this would
    generate a signed JWT or session cookie.
    """
    username = payload.username.strip().lower()
    user_record = _users_db.get(username)
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not pwd_context.verify(payload.password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    # Generate a fake token.  Replace with real JWT creation.
    token = f"fake-token-for-{username}"
    return {"access_token": token, "token_type": "bearer"}