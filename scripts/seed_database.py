#!/usr/bin/env python3
"""
Database Seeding Script - ITEM 12

Populates the database with default data:
- Default admin user (admin@cerebrum.ai)
- Sample construction projects
- Test IFC metadata
- Demo user roles

Usage:
    python scripts/seed_database.py [--reset]

Options:
    --reset: Drop all tables and recreate (WARNING: destroys all data)
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from uuid import uuid4
import argparse
from backend.core.database_enhanced import SessionLocal, Base, engine
from backend.backend.models import User, Project
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def seed_users(db):
    """Create default users."""
    print("🌱 Seeding users...")

    # Default admin user
    admin = User(
        id=uuid4(),
        email="admin@cerebrum.ai",
        hashed_password=hash_password("admin123!"),  # Change in production!
        role="admin",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    # Sample project manager
    pm = User(
        id=uuid4(),
        email="pm@cerebrum.ai",
        hashed_password=hash_password("manager123!"),
        role="engineer",  # Closest to project manager
        is_active=True,
        created_at=datetime.utcnow(),
    )

    # Sample operator (field worker)
    operator = User(
        id=uuid4(),
        email="operator@cerebrum.ai",
        hashed_password=hash_password("operator123!"),
        role="operator",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    # Viewer (read-only stakeholder)
    viewer = User(
        id=uuid4(),
        email="viewer@cerebrum.ai",
        hashed_password=hash_password("viewer123!"),
        role="viewer",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    db.add_all([admin, pm, operator, viewer])
    db.commit()

    print(f"  ✓ Created {4} users")
    return admin, pm, operator, viewer


def seed_projects(db, admin_user, pm_user):
    """Create sample construction projects."""
    print("🌱 Seeding projects...")

    # Sample project 1: Heritage Quarter (Diriyah)
    heritage = Project(
        id=uuid4(),
        name="Heritage Quarter - Diriyah Gate",
        description="Restoration and development of heritage area in Diriyah, Saudi Arabia. "
                    "Includes traditional Najdi architecture with modern amenities.",
        drive_folder_id="sample-heritage-folder-id",
        created_by=admin_user.id,
        created_at=datetime.utcnow(),
    )

    # Sample project 2: Commercial Tower
    tower = Project(
        id=uuid4(),
        name="NEOM Commercial Tower A1",
        description="50-story mixed-use tower with office, retail, and residential components. "
                    "LEED Platinum target with advanced BIM coordination.",
        drive_folder_id="sample-tower-folder-id",
        created_by=pm_user.id,
        created_at=datetime.utcnow() - timedelta(days=30),
    )

    # Sample project 3: Infrastructure Project
    infra = Project(
        id=uuid4(),
        name="Riyadh Metro Line Extension",
        description="4.5km extension of Riyadh Metro with 3 new stations. "
                    "Tunneling and elevated sections with complex MEP systems.",
        drive_folder_id="sample-metro-folder-id",
        created_by=admin_user.id,
        created_at=datetime.utcnow() - timedelta(days=60),
    )

    db.add_all([heritage, tower, infra])
    db.commit()

    print(f"  ✓ Created {3} projects")
    return heritage, tower, infra


def seed_ifc_metadata(db):
    """Create sample IFC metadata (placeholder for future IFC models)."""
    print("🌱 Seeding IFC metadata...")

    # Note: IFC models will be added in Phase 3 (Items 111-130)
    # This is a placeholder for future implementation

    print("  ✓ IFC metadata seeding prepared (full implementation in Phase 3)")


def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="Seed the Cerebrum database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate (WARNING: destroys all data)",
    )
    args = parser.parse_args()

    if args.reset:
        print("⚠️  WARNING: Dropping all tables...")
        response = input("Are you sure? This will delete all data. Type 'yes' to confirm: ")
        if response.lower() != "yes":
            print("Aborted.")
            return

        Base.metadata.drop_all(bind=engine)
        print("  ✓ All tables dropped")

    # Create all tables
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created")

    # Seed data
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@cerebrum.ai").first()
        if existing_admin and not args.reset:
            print("⚠️  Admin user already exists. Use --reset to recreate all data.")
            return

        admin, pm, operator, viewer = seed_users(db)
        heritage, tower, infra = seed_projects(db, admin, pm)
        seed_ifc_metadata(db)

        print("\n✅ Database seeding complete!")
        print("\n📝 Default Login Credentials:")
        print("   Admin:    admin@cerebrum.ai    / admin123!")
        print("   Manager:  pm@cerebrum.ai       / manager123!")
        print("   Operator: operator@cerebrum.ai / operator123!")
        print("   Viewer:   viewer@cerebrum.ai   / viewer123!")
        print("\n⚠️  Remember to change these passwords in production!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
