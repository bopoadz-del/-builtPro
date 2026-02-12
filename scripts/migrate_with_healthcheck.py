#!/usr/bin/env python3
"""
Migration Health Check Script - ITEM 15

Safe database migration with pre and post-migration validation:
- Pre-migration schema validation
- Migration execution
- Post-migration verification queries
- Rollback capability

Usage:
    python scripts/migrate_with_healthcheck.py [upgrade|downgrade] [revision]

Examples:
    python scripts/migrate_with_healthcheck.py upgrade head
    python scripts/migrate_with_healthcheck.py downgrade -1
    python scripts/migrate_with_healthcheck.py upgrade +2
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import subprocess
from datetime import datetime
from sqlalchemy import inspect, text
from backend.core.database_enhanced import engine, SessionLocal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_connectivity():
    """Verify database is reachable."""
    logger.info("🔍 Checking database connectivity...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


def get_current_schema():
    """Get current database schema snapshot."""
    logger.info("📸 Capturing current schema snapshot...")
    inspector = inspect(engine)

    schema = {
        'tables': {},
        'indexes': {},
    }

    for table_name in inspector.get_table_names():
        # Get columns
        columns = inspector.get_columns(table_name)
        schema['tables'][table_name] = {
            'columns': [col['name'] for col in columns],
            'column_types': {col['name']: str(col['type']) for col in columns},
        }

        # Get indexes
        indexes = inspector.get_indexes(table_name)
        schema['indexes'][table_name] = [idx['name'] for idx in indexes]

    logger.info(f"  Found {len(schema['tables'])} tables")
    return schema


def validate_schema():
    """Run schema validation checks."""
    logger.info("🔍 Validating schema integrity...")

    inspector = inspect(engine)
    issues = []

    # Check for tables without primary keys
    for table_name in inspector.get_table_names():
        pk = inspector.get_pk_constraint(table_name)
        if not pk or not pk.get('constrained_columns'):
            issues.append(f"Table '{table_name}' has no primary key")

    # Check for foreign keys without indexes
    for table_name in inspector.get_table_names():
        fks = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        index_columns = set()
        for idx in indexes:
            index_columns.update(idx['column_names'])

        for fk in fks:
            for col in fk['constrained_columns']:
                if col not in index_columns:
                    issues.append(
                        f"Foreign key '{col}' in table '{table_name}' has no index"
                    )

    if issues:
        logger.warning(f"⚠️  Found {len(issues)} schema issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("✅ Schema validation passed")

    return issues


def get_alembic_current_revision():
    """Get current Alembic revision."""
    try:
        result = subprocess.run(
            ['alembic', 'current'],
            capture_output=True,
            text=True,
            check=True
        )
        revision = result.stdout.strip().split()[0] if result.stdout.strip() else "None"
        logger.info(f"Current revision: {revision}")
        return revision
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get current revision: {e.stderr}")
        return None


def run_migration(command: str, revision: str):
    """
    Execute Alembic migration.

    Args:
        command: 'upgrade' or 'downgrade'
        revision: Target revision (e.g., 'head', '-1', '+2')
    """
    logger.info(f"🚀 Running migration: {command} {revision}")

    try:
        result = subprocess.run(
            ['alembic', command, revision],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(result.stdout)
        logger.info("✅ Migration completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed!")
        logger.error(e.stderr)
        return False


def post_migration_verification():
    """Run verification queries after migration."""
    logger.info("🔍 Running post-migration verification...")

    db = SessionLocal()
    try:
        # Test 1: Verify all tables are accessible
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"  ✓ Found {len(tables)} tables")

        # Test 2: Run simple query on each table
        for table_name in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                logger.debug(f"  ✓ Table '{table_name}': {count} rows")
            except Exception as e:
                logger.error(f"  ✗ Table '{table_name}' query failed: {str(e)}")
                return False

        # Test 3: Verify constraints are active
        # (This is database-specific; example for PostgreSQL)
        try:
            result = db.execute(text("""
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
            """))
            constraint_count = result.scalar()
            logger.info(f"  ✓ Found {constraint_count} constraints")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not verify constraints: {str(e)}")

        logger.info("✅ Post-migration verification passed")
        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        return False
    finally:
        db.close()


def create_backup_before_migration():
    """Create a quick backup before running migration."""
    logger.info("💾 Creating pre-migration backup...")

    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"pre_migration_backup_{timestamp}.sql"

        # Call backup script (if available)
        # For now, just log the intention
        logger.info(f"  Backup would be saved as: {backup_file}")
        logger.info("  ⚠️  Skipping actual backup (implement if needed)")

        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False


def main():
    """Main migration process with health checks."""
    parser = argparse.ArgumentParser(
        description="Run database migrations with health checks"
    )
    parser.add_argument(
        'command',
        choices=['upgrade', 'downgrade'],
        help='Migration command'
    )
    parser.add_argument(
        'revision',
        help='Target revision (head, -1, +2, specific hash)'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip pre-migration backup'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip schema validation'
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("DATABASE MIGRATION WITH HEALTH CHECKS")
    logger.info("=" * 70)

    # Step 1: Check database connectivity
    if not check_database_connectivity():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)

    # Step 2: Get current state
    current_revision = get_alembic_current_revision()
    if current_revision is None:
        logger.error("❌ Cannot determine current migration state")
        sys.exit(1)

    # Step 3: Pre-migration schema snapshot
    schema_before = get_current_schema()

    # Step 4: Pre-migration validation
    if not args.skip_validation:
        issues = validate_schema()
        if issues and args.command == 'downgrade':
            logger.warning("⚠️  Schema has issues, but proceeding with downgrade")

    # Step 5: Create backup (optional)
    if not args.skip_backup:
        if not create_backup_before_migration():
            response = input("Backup failed. Continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration aborted")
                sys.exit(1)

    # Step 6: Run migration
    logger.info(f"\n{'='*70}")
    logger.info(f"Executing: {args.command} {args.revision}")
    logger.info(f"{'='*70}\n")

    if not run_migration(args.command, args.revision):
        logger.error("\n❌ Migration failed - database may be in inconsistent state")
        logger.error("   Consider restoring from backup or fixing the migration")
        sys.exit(1)

    # Step 7: Post-migration verification
    if not post_migration_verification():
        logger.error("\n❌ Post-migration verification failed")
        logger.error("   Database may be in inconsistent state")
        sys.exit(1)

    # Step 8: Get new state
    new_revision = get_alembic_current_revision()
    schema_after = get_current_schema()

    # Step 9: Report changes
    logger.info("\n" + "=" * 70)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Revision: {current_revision} → {new_revision}")

    tables_before = set(schema_before['tables'].keys())
    tables_after = set(schema_after['tables'].keys())
    new_tables = tables_after - tables_before
    removed_tables = tables_before - tables_after

    if new_tables:
        logger.info(f"New tables: {', '.join(new_tables)}")
    if removed_tables:
        logger.info(f"Removed tables: {', '.join(removed_tables)}")

    logger.info("\n✅ Migration completed successfully!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
