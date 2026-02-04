"""
Database configuration and dependency.

This module defines the SQLAlchemy engine, session factory and a
``get_db`` dependency for FastAPI endpoints.  It reads the
``DATABASE_URL`` environment variable for connectivity.  Connection
pool parameters are set for enterprise workloads.  For SQLite
fallback in local development, use ``sqlite:///./test.db``.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Determine the database URL.  Render and other deployment platforms
# should set this environment variable.  In development it can be
# configured via a local `.env` file or default to SQLite.  The
# ``pool_pre_ping`` option ensures connections are validated before
# each use.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Additional engine options for connection pooling.  Adjust pool_size
# and max_overflow based on your deployment's requirements.  See
# SQLAlchemy documentation for details.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("POOL_SIZE", "10")),
    max_overflow=int(os.getenv("MAX_OVERFLOW", "20")),
    future=True,
)

# Create a session factory bound to the engine.  We disable
# autocommit and autoflush so transactions are explicit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """Yield a SQLAlchemy session.

    This function is a FastAPI dependency.  It opens a new database
    session for the request and ensures it is closed afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()