"""
Enhanced Configuration Management - ITEM 9

Pydantic Settings with strict validation for 40+ environment variables.
Fail-fast on startup if critical configuration is missing.

This ensures the application won't start with incomplete configuration.
"""

from typing import List, Optional
from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TenantIsolationMode(str, Enum):
    """Multi-tenancy isolation strategy."""
    SCHEMA = "schema"  # Separate PostgreSQL schemas per tenant
    RLS = "rls"  # Row-Level Security with tenant_id


class Settings(BaseSettings):
    """
    Comprehensive application settings with validation.

    All settings are loaded from environment variables.
    Critical settings will cause startup failure if missing.
    """

    # ========================================================================
    # CORE APPLICATION SETTINGS
    # ========================================================================
    app_name: str = Field(default="Cerebrum", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_v1_prefix: str = Field(default="/api/v1", description="API version prefix")

    # ========================================================================
    # DATABASE CONFIGURATION (Items 1-2)
    # ========================================================================
    database_url: str = Field(
        ...,  # Required field
        description="PostgreSQL connection string"
    )
    db_user: Optional[str] = Field(default=None, description="Database username")
    db_password: Optional[SecretStr] = Field(default=None, description="Database password")
    db_name: Optional[str] = Field(default=None, description="Database name")
    db_host: Optional[str] = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")

    # Connection Pooling (Item 1)
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=0, ge=0, le=100, description="Max overflow connections")
    pool_recycle: int = Field(default=3600, ge=300, description="Pool recycle time (seconds)")
    pool_timeout: int = Field(default=30, ge=5, le=120, description="Pool timeout (seconds)")
    sql_echo: bool = Field(default=False, description="Echo SQL queries")

    # PgBouncer (Item 2)
    pgbouncer_url: Optional[str] = Field(default=None, description="PgBouncer connection string")

    # ========================================================================
    # REDIS CONFIGURATION (Item 3)
    # ========================================================================
    redis_cache_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis cache database"
    )
    redis_queue_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis queue database (Celery)"
    )
    redis_session_url: str = Field(
        default="redis://localhost:6379/2",
        description="Redis session database"
    )
    redis_ratelimit_url: str = Field(
        default="redis://localhost:6379/3",
        description="Redis rate limit database"
    )

    # ========================================================================
    # SECURITY & AUTHENTICATION (Items 16-30)
    # ========================================================================
    secret_key: SecretStr = Field(
        ...,  # Required
        min_length=32,
        description="Application secret key (min 32 chars)"
    )
    jwt_secret_key: SecretStr = Field(
        ...,  # Required
        min_length=32,
        description="JWT signing key (min 32 chars)"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Access token expiry (minutes)"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry (days)"
    )

    # Password Security (Item 17)
    bcrypt_salt_rounds: int = Field(
        default=12,
        ge=10,
        le=16,
        description="BCrypt salt rounds"
    )
    password_pepper: Optional[SecretStr] = Field(
        default=None,
        description="Additional password HMAC pepper"
    )

    # Session Management (Item 25)
    session_expire_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Session expiry (hours)"
    )
    session_cookie_secure: bool = Field(
        default=True,
        description="Secure session cookies (HTTPS only)"
    )
    session_cookie_httponly: bool = Field(
        default=True,
        description="HTTP-only session cookies"
    )
    session_cookie_samesite: str = Field(
        default="strict",
        description="SameSite cookie policy"
    )

    # MFA (Item 24)
    mfa_issuer_name: str = Field(
        default="Cerebrum",
        description="TOTP issuer name"
    )
    mfa_backup_codes_count: int = Field(
        default=10,
        ge=5,
        le=20,
        description="Number of backup codes"
    )

    # OAuth2 (Item 26)
    google_client_id: Optional[str] = Field(default=None, description="Google OAuth client ID")
    google_client_secret: Optional[SecretStr] = Field(default=None, description="Google OAuth secret")
    microsoft_client_id: Optional[str] = Field(default=None, description="Microsoft OAuth client ID")
    microsoft_client_secret: Optional[SecretStr] = Field(default=None, description="Microsoft OAuth secret")

    # ========================================================================
    # BACKUP & RECOVERY (Items 13-14)
    # ========================================================================
    s3_backup_bucket: Optional[str] = Field(default=None, description="S3 backup bucket")
    s3_backup_prefix: str = Field(default="daily/", description="S3 backup prefix")
    backup_retention_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Backup retention (days)"
    )
    gpg_passphrase: Optional[SecretStr] = Field(
        default=None,
        description="GPG encryption passphrase"
    )

    # ========================================================================
    # SECRETS MANAGEMENT (Item 10)
    # ========================================================================
    vault_addr: Optional[str] = Field(default=None, description="HashiCorp Vault address")
    vault_token: Optional[SecretStr] = Field(default=None, description="Vault token")
    vault_db_mount: str = Field(default="database", description="Vault database mount")
    vault_db_role: str = Field(default="cerebrum-app", description="Vault database role")

    # ========================================================================
    # AWS / CLOUD SERVICES
    # ========================================================================
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[SecretStr] = Field(default=None, description="AWS secret key")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket: Optional[str] = Field(default=None, description="S3 uploads bucket")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    # ========================================================================
    # EXTERNAL AI SERVICES
    # ========================================================================
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    openai_max_tokens: int = Field(default=4096, ge=100, le=128000, description="Max tokens")
    openai_temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature")

    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic API key")

    # ========================================================================
    # GOOGLE SERVICES (Items 101-110)
    # ========================================================================
    google_drive_client_id: Optional[str] = Field(default=None, description="Google Drive OAuth client")
    google_drive_client_secret: Optional[SecretStr] = Field(default=None, description="Google Drive OAuth secret")
    google_drive_redirect_uri: Optional[str] = Field(default=None, description="OAuth redirect URI")

    # ========================================================================
    # ML & MLOPS (Items 166-185)
    # ========================================================================
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        description="MLflow tracking server"
    )
    model_registry_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket for model artifacts"
    )
    model_signing_key: Optional[SecretStr] = Field(
        default=None,
        description="Model signing secret key"
    )

    # ========================================================================
    # VECTOR DATABASES & EMBEDDINGS
    # ========================================================================
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8000, ge=1, le=65535, description="ChromaDB port")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    embedding_dimension: int = Field(default=384, ge=128, le=4096, description="Embedding dimension")

    # ========================================================================
    # MULTI-TENANCY (Items 281-300)
    # ========================================================================
    tenant_isolation_mode: TenantIsolationMode = Field(
        default=TenantIsolationMode.RLS,
        description="Tenant isolation strategy"
    )
    default_tenant_id: str = Field(default="default", description="Default tenant ID")
    subdomain_enabled: bool = Field(default=True, description="Enable subdomain routing")
    base_domain: str = Field(default="cerebrum.ai", description="Base domain")

    # ========================================================================
    # MONITORING & OBSERVABILITY (Items 341-365)
    # ========================================================================
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    sentry_environment: Optional[str] = Field(default=None, description="Sentry environment")
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry trace sampling rate"
    )

    datadog_api_key: Optional[SecretStr] = Field(default=None, description="Datadog API key")
    datadog_app_key: Optional[SecretStr] = Field(default=None, description="Datadog app key")

    # ========================================================================
    # RATE LIMITING (Item 43)
    # ========================================================================
    rate_limit_global: int = Field(default=100, ge=10, le=10000, description="Global rate limit")
    rate_limit_auth: int = Field(default=5, ge=1, le=100, description="Auth rate limit")
    rate_limit_ifc_processing: int = Field(default=10, ge=1, le=100, description="IFC rate limit")
    rate_limit_admin: int = Field(default=50, ge=10, le=1000, description="Admin rate limit")

    # ========================================================================
    # SECURITY HEADERS & POLICIES (Items 41-42)
    # ========================================================================
    hsts_max_age: int = Field(default=31536000, ge=0, description="HSTS max age")
    csp_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        description="Content Security Policy"
    )
    cors_allow_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS credentials")

    # ========================================================================
    # COMPLIANCE (Item 50)
    # ========================================================================
    soc2_enabled: bool = Field(default=False, description="SOC 2 compliance mode")
    gdpr_enabled: bool = Field(default=False, description="GDPR compliance mode")
    data_retention_audit_years: int = Field(
        default=7,
        ge=1,
        le=10,
        description="Audit log retention (years)"
    )
    data_retention_temp_years: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Temp file retention (years)"
    )
    compliance_region: str = Field(default="US", description="Compliance region")

    # ========================================================================
    # CELERY CONFIGURATION (Items 241-242)
    # ========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend"
    )
    celery_queue_fast: str = Field(default="celery_fast", description="Fast queue name")
    celery_queue_slow: str = Field(default="celery_slow", description="Slow queue name")
    celery_queue_beats: str = Field(default="celery_beats", description="Beats queue name")

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL")
    max_upload_size_mb: int = Field(default=100, ge=1, le=1000, description="Max upload size (MB)")

    # IFC Processing (Items 111-130)
    ifc_processing_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="IFC processing timeout (seconds)"
    )
    ifc_max_file_size_mb: int = Field(
        default=500,
        ge=10,
        le=5000,
        description="Max IFC file size (MB)"
    )
    draco_compression_enabled: bool = Field(
        default=True,
        description="Enable Draco compression"
    )

    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    feature_smart_context: bool = Field(default=True, description="Smart context feature")
    feature_edge_computing: bool = Field(default=False, description="Edge computing feature")
    feature_digital_twin: bool = Field(default=False, description="Digital twin feature")
    feature_vdc: bool = Field(default=True, description="VDC feature")
    feature_subcontractor_portal: bool = Field(
        default=False,
        description="Subcontractor portal feature"
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is PostgreSQL."""
        if v.startswith("postgres://"):
            # Render.com compatibility
            v = v.replace("postgres://", "postgresql://", 1)
        if not v.startswith("postgresql://") and not v.startswith("sqlite://"):
            raise ValueError("DATABASE_URL must be PostgreSQL or SQLite")
        return v

    @field_validator('cors_allow_origins', mode='before')
    @classmethod
    def split_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ========================================================================
    # PYDANTIC CONFIGURATION
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def redis_url(self) -> str:
        """Legacy compatibility: default Redis URL."""
        return self.redis_cache_url


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================
try:
    settings = Settings()
    print("✅ Configuration loaded successfully")
    print(f"   Environment: {settings.environment}")
    print(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'SQLite'}")
    print(f"   Debug mode: {settings.debug}")
except Exception as e:
    print(f"❌ Configuration validation failed: {str(e)}")
    print("   Check your .env file and ensure all required variables are set")
    raise


# Export
__all__ = ["settings", "Settings", "Environment"]
