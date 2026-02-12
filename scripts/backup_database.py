#!/usr/bin/env python3
"""
Database Backup Script - ITEM 13

Automated database backup with:
- pg_dump to create SQL backup
- S3 upload with GPG encryption
- 30-day retention policy
- Cron schedule: Daily at 2 AM

Cron Configuration:
    0 2 * * * /usr/bin/python3 /app/scripts/backup_database.py

Environment Variables Required:
    DATABASE_URL: PostgreSQL connection string
    S3_BACKUP_BUCKET: S3 bucket name (e.g., cerebrum-backups)
    S3_BACKUP_PREFIX: S3 key prefix (e.g., daily/)
    GPG_PASSPHRASE: Encryption passphrase
    AWS_ACCESS_KEY_ID: AWS credentials
    AWS_SECRET_ACCESS_KEY: AWS credentials
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import tempfile
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_database_url(url: str) -> dict:
    """Parse DATABASE_URL into components."""
    parsed = urlparse(url)
    return {
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
    }


def create_backup() -> str:
    """
    Create PostgreSQL backup using pg_dump.

    Returns:
        Path to backup file
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    db_config = parse_database_url(database_url)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"cerebrum_backup_{timestamp}.sql"
    backup_path = os.path.join(tempfile.gettempdir(), backup_filename)

    logger.info(f"Creating backup: {backup_filename}")

    # Set environment for pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']

    # Execute pg_dump
    cmd = [
        'pg_dump',
        '-h', db_config['host'],
        '-p', str(db_config['port']),
        '-U', db_config['user'],
        '-d', db_config['database'],
        '-F', 'p',  # Plain SQL format
        '-f', backup_path,
        '--verbose',
        '--no-owner',  # Don't include ownership commands
        '--no-acl',  # Don't include ACL commands
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logger.info(f"Backup created successfully: {backup_path}")

        # Get file size
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        logger.info(f"Backup size: {size_mb:.2f} MB")

        return backup_path

    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr}")
        raise


def encrypt_backup(backup_path: str) -> str:
    """
    Encrypt backup file using GPG.

    Args:
        backup_path: Path to unencrypted backup

    Returns:
        Path to encrypted backup
    """
    gpg_passphrase = os.getenv("GPG_PASSPHRASE")
    if not gpg_passphrase:
        raise ValueError("GPG_PASSPHRASE not set")

    encrypted_path = f"{backup_path}.gpg"
    logger.info("Encrypting backup...")

    cmd = [
        'gpg',
        '--symmetric',
        '--cipher-algo', 'AES256',
        '--batch',
        '--yes',
        '--passphrase', gpg_passphrase,
        '--output', encrypted_path,
        backup_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Backup encrypted: {encrypted_path}")

        # Remove unencrypted file
        os.remove(backup_path)
        logger.info("Removed unencrypted backup")

        return encrypted_path

    except subprocess.CalledProcessError as e:
        logger.error(f"GPG encryption failed: {e.stderr}")
        raise


def upload_to_s3(file_path: str) -> str:
    """
    Upload encrypted backup to S3.

    Args:
        file_path: Path to encrypted backup

    Returns:
        S3 key of uploaded file
    """
    bucket = os.getenv("S3_BACKUP_BUCKET")
    prefix = os.getenv("S3_BACKUP_PREFIX", "daily/")

    if not bucket:
        raise ValueError("S3_BACKUP_BUCKET not set")

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("boto3 not installed. Run: pip install boto3")
        raise

    s3_client = boto3.client('s3')
    filename = os.path.basename(file_path)
    s3_key = os.path.join(prefix, filename)

    logger.info(f"Uploading to S3: s3://{bucket}/{s3_key}")

    try:
        s3_client.upload_file(file_path, bucket, s3_key)
        logger.info("Upload successful")

        # Remove local encrypted file
        os.remove(file_path)
        logger.info("Removed local encrypted backup")

        return s3_key

    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}")
        raise


def cleanup_old_backups():
    """
    Delete S3 backups older than 30 days.
    """
    bucket = os.getenv("S3_BACKUP_BUCKET")
    prefix = os.getenv("S3_BACKUP_PREFIX", "daily/")
    retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    if not bucket:
        logger.warning("S3_BACKUP_BUCKET not set, skipping cleanup")
        return

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.warning("boto3 not installed, skipping cleanup")
        return

    s3_client = boto3.client('s3')
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    logger.info(f"Cleaning up backups older than {retention_days} days...")

    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' not in response:
            logger.info("No backups found")
            return

        deleted_count = 0
        for obj in response['Contents']:
            if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                logger.info(f"Deleting old backup: {obj['Key']}")
                s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
                deleted_count += 1

        logger.info(f"Deleted {deleted_count} old backup(s)")

    except ClientError as e:
        logger.error(f"Cleanup failed: {str(e)}")


def verify_backup(s3_key: str) -> bool:
    """
    Verify backup exists in S3 and has non-zero size.

    Args:
        s3_key: S3 key to verify

    Returns:
        True if backup is valid
    """
    bucket = os.getenv("S3_BACKUP_BUCKET")

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.warning("boto3 not installed, skipping verification")
        return False

    s3_client = boto3.client('s3')

    try:
        response = s3_client.head_object(Bucket=bucket, Key=s3_key)
        size = response['ContentLength']

        if size > 0:
            logger.info(f"Backup verified: {size / (1024*1024):.2f} MB")
            return True
        else:
            logger.error("Backup file is empty!")
            return False

    except ClientError as e:
        logger.error(f"Verification failed: {str(e)}")
        return False


def main():
    """Main backup process."""
    logger.info("=" * 60)
    logger.info("Starting database backup process")
    logger.info("=" * 60)

    try:
        # Step 1: Create backup
        backup_path = create_backup()

        # Step 2: Encrypt backup
        encrypted_path = encrypt_backup(backup_path)

        # Step 3: Upload to S3
        s3_key = upload_to_s3(encrypted_path)

        # Step 4: Verify upload
        if verify_backup(s3_key):
            logger.info("✅ Backup completed successfully")
        else:
            logger.error("❌ Backup verification failed")
            sys.exit(1)

        # Step 5: Cleanup old backups
        cleanup_old_backups()

        logger.info("=" * 60)
        logger.info("Backup process complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
