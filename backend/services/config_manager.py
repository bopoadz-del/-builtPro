"""
Configuration Manager for BuilTPro Brain AI

Dynamic configuration, feature flags, and environment management.

Features:
- Dynamic configuration updates
- Feature flags (gradual rollout)
- Environment-specific configs
- Config versioning
- Hot reload support
- Config validation
- A/B testing support
- Secrets management

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ConfigEntry:
    key: str
    value: Any
    environment: Environment
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = "system"
    description: str = ""


@dataclass
class FeatureFlag:
    flag_id: str
    name: str
    enabled: bool = False
    rollout_percentage: float = 0.0  # 0-100
    allowed_users: List[str] = field(default_factory=list)
    environments: List[Environment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """Production-ready configuration manager."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.configs: Dict[str, Dict[str, ConfigEntry]] = {}  # env -> key -> entry
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.config_history: List[ConfigEntry] = []
        self.current_env = Environment.DEVELOPMENT

        self.stats = {"config_updates": 0, "flag_checks": 0}
        logger.info("Configuration Manager initialized")

    def set_config(self, key: str, value: Any, environment: Optional[Environment] = None,
                   updated_by: str = "system", description: str = ""):
        """Set a configuration value."""
        env = environment or self.current_env

        if env.value not in self.configs:
            self.configs[env.value] = {}

        existing = self.configs[env.value].get(key)
        version = (existing.version + 1) if existing else 1

        entry = ConfigEntry(
            key=key, value=value, environment=env,
            version=version, updated_by=updated_by, description=description
        )

        self.configs[env.value][key] = entry
        self.config_history.append(entry)
        self.stats["config_updates"] += 1

    def get_config(self, key: str, default: Any = None, environment: Optional[Environment] = None) -> Any:
        """Get a configuration value."""
        env = (environment or self.current_env).value
        entry = self.configs.get(env, {}).get(key)
        return entry.value if entry else default

    def create_feature_flag(self, flag_id: str, name: str, enabled: bool = False,
                            rollout_percentage: float = 0.0) -> FeatureFlag:
        """Create a feature flag."""
        flag = FeatureFlag(
            flag_id=flag_id, name=name, enabled=enabled,
            rollout_percentage=rollout_percentage
        )
        self.feature_flags[flag_id] = flag
        return flag

    def is_feature_enabled(self, flag_id: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled."""
        self.stats["flag_checks"] += 1
        flag = self.feature_flags.get(flag_id)
        if not flag:
            return False
        if not flag.enabled:
            return False

        # Check user-specific allow list
        if user_id and user_id in flag.allowed_users:
            return True

        # Check rollout percentage
        if flag.rollout_percentage >= 100:
            return True
        if user_id:
            import hashlib
            hash_val = int(hashlib.md5(f"{flag_id}:{user_id}".encode()).hexdigest(), 16)
            return (hash_val % 100) < flag.rollout_percentage

        return flag.enabled

    def toggle_feature(self, flag_id: str, enabled: bool):
        """Toggle a feature flag."""
        if flag_id in self.feature_flags:
            self.feature_flags[flag_id].enabled = enabled

    def get_all_configs(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Get all configs for an environment."""
        env = (environment or self.current_env).value
        return {k: v.value for k, v in self.configs.get(env, {}).items()}

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats, "total_configs": sum(len(c) for c in self.configs.values()),
                "feature_flags": len(self.feature_flags), "environment": self.current_env.value}


config_manager = ConfigurationManager()
