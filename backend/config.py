"""
Centralized configuration for the Diriyah Brain AI backend.

This module defines a Settings class compatible with both Pydantic v1 and v2
(via pydantic-settings when available). Environment variables are mapped by
field name (e.g., JWT_SECRET_KEY -> jwt_secret_key).
"""

from __future__ import annotations

from typing import List, Optional

try:
    # Pydantic v2 style
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator

    _V2 = True
except Exception:
    # Pydantic v1 fallback
    from pydantic import BaseSettings, Field, validator  # type: ignore

    SettingsConfigDict = None  # type: ignore
    _V2 = False


class Settings(BaseSettings):
    # General
    env: str = Field(default="production")

    # Secrets / keys
    openai_api_key: Optional[str] = Field(default=None)
    moonshot_api_key: Optional[str] = Field(default=None)
    kimi_model: str = Field(default="kimi-k2.5")
    kimi_max_tokens: int = Field(default=4096)
    kimi_base_url: str = Field(default="https://api.moonshot.ai/v1")
    jwt_secret_key: Optional[str] = Field(default=None)

    # CORS (comma-separated string or list)
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])

    # Service thresholds
    uncertainty_threshold: float = Field(default=0.3)
    causal_confidence_level: float = Field(default=0.9)

    # Infra
    redis_url: str = Field(default="redis://localhost:6379/0")
    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8000)

    if _V2:
        @field_validator("cors_allow_origins", mode="before")
        def _split_origins(cls, v):
            if v is None:
                return ["*"]
            if isinstance(v, str):
                parts = [p.strip() for p in v.split(",") if p.strip()]
                return parts or ["*"]
            return v
    else:
        @validator("cors_allow_origins", pre=True)  # type: ignore[misc]
        def _split_origins(cls, v):
            if v is None:
                return ["*"]
            if isinstance(v, str):
                parts = [p.strip() for p in v.split(",") if p.strip()]
                return parts or ["*"]
            return v

    # pydantic v2 config
    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # pydantic v1 config
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
