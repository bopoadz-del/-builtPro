"""
Data Encryption Utilities - ITEM 47

Field-level encryption for PII (Personally Identifiable Information):
- AES-256-GCM encryption for sensitive fields
- Key management with rotation support
- Transparent encryption/decryption in models
- PostgreSQL TDE (Transparent Data Encryption) - documented
- S3 SSE-KMS for file storage - documented

Security best practices:
- Unique initialization vector (IV) per encryption
- Authenticated encryption (GCM mode)
- Key versioning for rotation
- Secure key storage (environment variables / Vault)
"""

import os
import base64
import hashlib
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ITEM 47: Field-Level Encryption
# ============================================================================

class FieldEncryption:
    """
    AES-256-GCM encryption for sensitive database fields.

    Encrypts PII fields (email, phone, SSN) before storage and
    decrypts on retrieval.
    """

    def __init__(self, master_key: str = None, key_version: int = 1):
        """
        Initialize field encryption.

        Args:
            master_key: Master encryption key (from env or Vault)
            key_version: Key version for rotation support
        """
        self.key_version = key_version
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")

        if not self.master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY not set")

        # Derive encryption key from master key using PBKDF2
        self.encryption_key = self._derive_key(self.master_key)

        # Initialize AESGCM cipher
        self.cipher = AESGCM(self.encryption_key)

    def _derive_key(self, master_key: str, salt: bytes = None) -> bytes:
        """
        Derive encryption key from master key using PBKDF2.

        Args:
            master_key: Master key string
            salt: Optional salt (uses fixed salt for consistency)

        Returns:
            32-byte encryption key
        """
        # Use fixed salt for key derivation (in production, use Vault)
        salt = salt or b"cerebrum-encryption-salt-v1"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )

        return kdf.derive(master_key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: Text to encrypt

        Returns:
            Base64-encoded ciphertext with format: version:iv:ciphertext

        Example:
            >>> enc = FieldEncryption()
            >>> encrypted = enc.encrypt("john@example.com")
            >>> print(encrypted)
            1:YWJjZGVm:ZW5jcnlwdGVkZGF0YQ==
        """
        if not plaintext:
            return ""

        # Generate random 96-bit IV (nonce)
        iv = os.urandom(12)

        # Encrypt with authenticated encryption (GCM)
        ciphertext = self.cipher.encrypt(
            nonce=iv,
            data=plaintext.encode("utf-8"),
            associated_data=None,
        )

        # Encode as base64
        iv_b64 = base64.b64encode(iv).decode("ascii")
        ciphertext_b64 = base64.b64encode(ciphertext).decode("ascii")

        # Format: version:iv:ciphertext
        return f"{self.key_version}:{iv_b64}:{ciphertext_b64}"

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted text (format: version:iv:ciphertext)

        Returns:
            Decrypted plaintext string

        Example:
            >>> enc = FieldEncryption()
            >>> decrypted = enc.decrypt("1:YWJjZGVm:ZW5jcnlwdGVkZGF0YQ==")
            >>> print(decrypted)
            john@example.com
        """
        if not ciphertext:
            return ""

        try:
            # Parse format: version:iv:ciphertext
            parts = ciphertext.split(":", 2)
            if len(parts) != 3:
                raise ValueError("Invalid ciphertext format")

            version, iv_b64, ciphertext_b64 = parts

            # Decode from base64
            iv = base64.b64decode(iv_b64)
            ciphertext_bytes = base64.b64decode(ciphertext_b64)

            # Decrypt
            plaintext_bytes = self.cipher.decrypt(
                nonce=iv,
                data=ciphertext_bytes,
                associated_data=None,
            )

            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt field")


# ============================================================================
# Global Encryptor Instance
# ============================================================================

# Singleton instance (initialized on first use)
_encryptor: Optional[FieldEncryption] = None


def get_encryptor() -> FieldEncryption:
    """
    Get global field encryptor instance.

    Returns:
        FieldEncryption instance
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = FieldEncryption()
    return _encryptor


# ============================================================================
# Convenience Functions
# ============================================================================

def encrypt_field(value: str) -> str:
    """
    Encrypt a field value.

    Args:
        value: Plaintext value

    Returns:
        Encrypted value

    Usage:
        encrypted_email = encrypt_field("john@example.com")
    """
    return get_encryptor().encrypt(value)


def decrypt_field(value: str) -> str:
    """
    Decrypt a field value.

    Args:
        value: Encrypted value

    Returns:
        Decrypted plaintext

    Usage:
        email = decrypt_field(user.encrypted_email)
    """
    return get_encryptor().decrypt(value)


# ============================================================================
# SQLAlchemy Column Type for Encrypted Fields
# ============================================================================

from sqlalchemy.types import TypeDecorator, String


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy column type for automatic encryption/decryption.

    Usage:
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            email = Column(EncryptedString(255), unique=True)
            phone = Column(EncryptedString(50))

    When reading/writing, encryption is automatic:
        user = User(email="john@example.com")  # Automatically encrypted
        print(user.email)  # Automatically decrypted
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value when reading from database."""
        if value is not None:
            return decrypt_field(value)
        return value


# ============================================================================
# Hash-Based Field Encryption (for searching)
# ============================================================================

def hash_for_search(value: str) -> str:
    """
    Create searchable hash of encrypted field.

    Allows searching on encrypted fields without decrypting.
    Use separate column for hash.

    Args:
        value: Original value

    Returns:
        SHA-256 hash (hex)

    Usage:
        class User(Base):
            email = Column(EncryptedString(255))
            email_hash = Column(String(64), index=True)

        # On insert:
        user = User(
            email="john@example.com",
            email_hash=hash_for_search("john@example.com")
        )

        # On search:
        search_hash = hash_for_search("john@example.com")
        user = session.query(User).filter(User.email_hash == search_hash).first()
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ============================================================================
# ITEM 47: PostgreSQL TDE (Transparent Data Encryption)
# ============================================================================

"""
PostgreSQL TDE Configuration (Documentation):

1. **Enable pgcrypto Extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   ```

2. **Encrypted Columns**:
   ```sql
   CREATE TABLE users (
       id UUID PRIMARY KEY,
       email_encrypted BYTEA,  -- Store encrypted data
       email_hash VARCHAR(64) INDEX  -- For searching
   );
   ```

3. **Encrypt on Insert**:
   ```sql
   INSERT INTO users (id, email_encrypted, email_hash)
   VALUES (
       gen_random_uuid(),
       pgp_sym_encrypt('john@example.com', 'encryption-key'),
       encode(digest('john@example.com', 'sha256'), 'hex')
   );
   ```

4. **Decrypt on Select**:
   ```sql
   SELECT
       id,
       pgp_sym_decrypt(email_encrypted, 'encryption-key') as email
   FROM users;
   ```

5. **PostgreSQL 15+ Built-in TDE**:
   - Enable cluster-wide encryption with initdb --data-checksums
   - Use encrypted tablespaces
   - Configure ssl_key and ssl_cert for connections
"""


# ============================================================================
# ITEM 47: S3 Server-Side Encryption (SSE-KMS)
# ============================================================================

"""
S3 SSE-KMS Configuration (Documentation):

1. **Create KMS Key** (AWS Console or CLI):
   ```bash
   aws kms create-key --description "Cerebrum S3 encryption key"
   ```

2. **Configure S3 Bucket** for Default Encryption:
   ```python
   import boto3

   s3 = boto3.client('s3')
   s3.put_bucket_encryption(
       Bucket='cerebrum-uploads',
       ServerSideEncryptionConfiguration={
           'Rules': [{
               'ApplyServerSideEncryptionByDefault': {
                   'SSEAlgorithm': 'aws:kms',
                   'KMSMasterKeyID': 'arn:aws:kms:region:account:key/key-id'
               }
           }]
       }
   )
   ```

3. **Upload with Encryption**:
   ```python
   s3.upload_file(
       Filename='file.pdf',
       Bucket='cerebrum-uploads',
       Key='documents/file.pdf',
       ExtraArgs={
           'ServerSideEncryption': 'aws:kms',
           'SSEKMSKeyId': 'arn:aws:kms:region:account:key/key-id'
       }
   )
   ```

4. **Boto3 Client Configuration**:
   ```python
   from backend.core.config_enhanced import settings

   s3_client = boto3.client(
       's3',
       aws_access_key_id=settings.aws_access_key_id,
       aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
       region_name=settings.s3_region,
       config=Config(
           signature_version='s3v4',
           s3={'addressing_style': 'path'}
       )
   )
   ```
"""


# ============================================================================
# Key Rotation Support
# ============================================================================

class KeyRotation:
    """
    Support for encryption key rotation.

    Allows re-encrypting data with new keys while maintaining
    backward compatibility with old keys.
    """

    def __init__(self):
        """Initialize key rotation manager."""
        self.keys = {
            1: FieldEncryption(key_version=1),  # Current key
            # Add old keys for backward compatibility:
            # 0: FieldEncryption(master_key=OLD_KEY, key_version=0),
        }
        self.current_version = 1

    def encrypt(self, plaintext: str) -> str:
        """Encrypt with current key version."""
        return self.keys[self.current_version].encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt with appropriate key version."""
        # Extract version from ciphertext
        version = int(ciphertext.split(":", 1)[0])

        if version not in self.keys:
            raise ValueError(f"Unknown key version: {version}")

        return self.keys[version].decrypt(ciphertext)

    def re_encrypt(self, old_ciphertext: str) -> str:
        """
        Re-encrypt data with current key.

        Use during key rotation to update old encrypted data.

        Args:
            old_ciphertext: Data encrypted with old key

        Returns:
            Data encrypted with current key
        """
        # Decrypt with old key
        plaintext = self.decrypt(old_ciphertext)

        # Encrypt with current key
        return self.encrypt(plaintext)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "FieldEncryption",
    "get_encryptor",
    "encrypt_field",
    "decrypt_field",
    "EncryptedString",
    "hash_for_search",
    "KeyRotation",
]
