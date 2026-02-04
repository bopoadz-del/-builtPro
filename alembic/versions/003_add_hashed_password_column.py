"""Add hashed_password column to users table

Revision ID: 003_add_hashed_password_column
Revises: 002_add_users_and_refresh_tokens
Create Date: 2026-02-04 00:00:00

This migration adds the hashed_password column to the users table if it
doesn't already exist. This handles the case where the users table was
created without this column, causing runtime errors when SQLAlchemy
attempts to query it.

The column is added as nullable (NULL) to avoid issues with existing
rows. Applications should ensure that hashed_password is populated
for all active users during or after this migration.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_hashed_password_column'
down_revision = '002_add_users_and_refresh_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add hashed_password column to users table if it doesn't exist."""
    # Use raw SQL with IF NOT EXISTS to make this migration idempotent
    # This avoids errors if the column already exists
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255) NULL
    """)


def downgrade() -> None:
    """Remove hashed_password column from users table if it exists."""
    # Use raw SQL with IF EXISTS to make downgrade idempotent
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS hashed_password
    """)
