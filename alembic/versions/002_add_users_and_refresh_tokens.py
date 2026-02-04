"""Add users and refresh_tokens tables

Revision ID: 002_add_users_and_refresh_tokens
Revises: 001_initial
Create Date: 2026-02-04 00:00:00

This Alembic migration introduces two new tables to support user
authentication and session management.  The ``users`` table stores
basic account information including a unique email address, a
``hashed_password`` column for securely stored credentials, a role
enum indicating the user's permissions, and timestamps for account
creation and last login.  The ``refresh_tokens`` table allows the
backend to issue and revoke refresh tokens for long‑lived sessions.

If your database already includes a ``users`` table without a
``hashed_password`` column, running this migration will fail.  In
that scenario you should either rename the existing column to
``hashed_password`` or perform an ``ALTER TABLE`` to add the
missing field.  See the documentation for details.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_users_and_refresh_tokens'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users and refresh_tokens tables."""
    # Create an enum type for the user role; matching values defined
    # in backend/app/models/auth.py (operator, engineer, admin, auditor, system).
    user_role = sa.Enum(
        'operator',
        'engineer',
        'admin',
        'auditor',
        'system',
        name='userrole',
    )
    user_role.create(op.get_bind(), checkfirst=True)

    # Create the users table with a hashed_password column
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='operator'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )

    # Index for quick lookup by email
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create the refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token', name='uq_refresh_tokens_token'),
    )

    # Index for quick lookup by token
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)


def downgrade() -> None:
    """Drop users and refresh_tokens tables along with the enum type."""
    op.drop_index('ix_refresh_tokens_token', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    # Drop the enum type.  Note: this must be done after dropping
    # dependent tables to avoid constraint errors.
    user_role = sa.Enum(
        'operator',
        'engineer',
        'admin',
        'auditor',
        'system',
        name='userrole',
    )
    user_role.drop(op.get_bind(), checkfirst=True)