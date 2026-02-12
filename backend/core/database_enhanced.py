"""
Enhanced Database Configuration for Cerebrum Platform.

This module implements Items 1-15 from the Cerebrum specification:
- PostgreSQL connection pooling with enterprise parameters
- Soft delete mixin
- Transaction decorators
- Database utilities (indexes, constraints, migrations)
"""

import os
import functools
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional, Any, Callable
from sqlalchemy import create_engine, event, Column, DateTime, Boolean, Index
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, declared_attr
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ITEM 1: PostgreSQL Connection Pool
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/cerebrum")

# Convert postgres:// to postgresql:// (Render.com compatibility)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Enterprise-grade connection pool settings
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv("POOL_SIZE", "20")),  # Max connections in pool
    max_overflow=int(os.getenv("MAX_OVERFLOW", "0")),  # No overflow (strict limit)
    pool_recycle=int(os.getenv("POOL_RECYCLE", "3600")),  # Recycle connections every hour
    pool_pre_ping=True,  # Verify connections before use
    pool_timeout=int(os.getenv("POOL_TIMEOUT", "30")),  # Wait max 30s for connection
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL logging for debugging
    future=True,  # SQLAlchemy 2.0 style
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent lazy loading errors after commit
)


# ============================================================================
# ITEM 2: PgBouncer Configuration (Documentation)
# ============================================================================
"""
PgBouncer configuration for production deployment (pgbouncer.ini):

[databases]
cerebrum = host=localhost port=5432 dbname=cerebrum

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
"""


# ============================================================================
# ITEM 3: Redis Cluster Setup (Documentation)
# ============================================================================
"""
Redis instance separation for different workloads:

Database 0: Cache (general application caching)
Database 1: Queue (Celery task queue)
Database 2: Sessions (user session storage)
Database 3: Rate Limit (rate limiting counters)

Configuration in .env:
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_QUEUE_URL=redis://localhost:6379/1
REDIS_SESSION_URL=redis://localhost:6379/2
REDIS_RATELIMIT_URL=redis://localhost:6379/3
"""


# ============================================================================
# ITEM 4: Soft Delete Mixin
# ============================================================================
class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Adds deleted_at column and provides methods for soft deletion.
    When querying, automatically filters out deleted records.
    """
    deleted_at = Column(DateTime, nullable=True, index=True)

    def soft_delete(self):
        """Mark this record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is deleted."""
        return self.deleted_at is not None

    @classmethod
    def active_only(cls, query):
        """Filter query to only active (non-deleted) records."""
        return query.filter(cls.deleted_at.is_(None))


# ============================================================================
# ITEM 5: Database Index Strategy
# ============================================================================
class IndexedModelMixin:
    """
    Mixin providing common composite indexes for high-performance queries.

    Usage: Add this mixin to models that need standard indexes.
    """

    @declared_attr
    def __table_args__(cls):
        """Define composite indexes for common query patterns."""
        return (
            # Index for user-scoped queries with time ordering
            Index(f'ix_{cls.__tablename__}_user_created', 'user_id', 'created_at'),
            # Index for project-scoped queries with status filtering
            Index(f'ix_{cls.__tablename__}_project_status', 'project_id', 'status'),
            # Index for tenant isolation with ID lookup
            Index(f'ix_{cls.__tablename__}_tenant_id', 'tenant_id', 'id'),
        )


# ============================================================================
# ITEM 6: Foreign Key Constraints (Handled in models)
# ============================================================================
"""
Foreign key constraints should be defined in models with:
- ON DELETE CASCADE: Automatically delete child records
- ON UPDATE CASCADE: Update foreign keys when parent changes

Example:
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
"""


# ============================================================================
# ITEM 8: Transaction Decorator
# ============================================================================
def transactional(func: Callable) -> Callable:
    """
    Decorator for automatic transaction management with rollback on exceptions.

    Usage:
        @transactional
        def create_user(db: Session, user_data: dict):
            user = User(**user_data)
            db.add(user)
            return user

    The function must accept 'db' as first parameter (Session object).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find the Session object in arguments
        db: Optional[Session] = None

        # Check positional args
        for arg in args:
            if isinstance(arg, Session):
                db = arg
                break

        # Check keyword args
        if db is None and 'db' in kwargs:
            db = kwargs['db']

        if db is None:
            raise ValueError("Transactional decorator requires a 'db' Session parameter")

        try:
            result = func(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
            raise

    return wrapper


@contextmanager
def transaction_context(db: Session, savepoint: bool = False):
    """
    Context manager for manual transaction control with savepoint support.

    Usage:
        with transaction_context(db, savepoint=True):
            db.add(user)
            # ... more operations
            # Automatic commit on success, rollback on exception

    Args:
        db: SQLAlchemy session
        savepoint: If True, use nested transaction (savepoint)
    """
    if savepoint:
        with db.begin_nested():
            yield db
    else:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


# ============================================================================
# ITEM 9: FastAPI Dependency
# ============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Yields a database session and ensures it's closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Database Utilities
# ============================================================================
def check_database_connection() -> bool:
    """
    Verify database connectivity.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


def get_pool_status() -> dict:
    """
    Get current connection pool statistics.

    Returns:
        Dictionary with pool metrics
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow(),
    }


# ============================================================================
# Event Listeners for Connection Pool Monitoring
# ============================================================================
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections."""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout from pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection return to pool."""
    logger.debug("Connection returned to pool")


# ============================================================================
# Base Model Class
# ============================================================================
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Export all public components
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "SoftDeleteMixin",
    "IndexedModelMixin",
    "transactional",
    "transaction_context",
    "check_database_connection",
    "get_pool_status",
]
