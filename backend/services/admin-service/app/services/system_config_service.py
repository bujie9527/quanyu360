"""System config business logic."""
from __future__ import annotations

from fastapi import HTTPException
from fastapi import status

from app.config import settings
from app.repositories.system_config_repository import SystemConfigRepository
from app.utils.config_crypto import decrypt_value
from app.utils.config_crypto import encrypt_value
from app.utils.config_crypto import mask_secret
from common.app.models import SystemConfig


class SystemConfigService:
    """Orchestrates system configuration."""

    def __init__(self, repo: SystemConfigRepository):
        self.repo = repo
        self._enc_key = settings.config_encryption_key
        self._fallback = settings.jwt_secret_key or "change-me"

    def list_configs(self, category: str | None = None) -> list[dict]:
        """List configs. Secrets are masked."""
        items = self.repo.list_all(category=category)
        return [self._to_response(c) for c in items]

    def get_config(self, key: str) -> dict:
        """Get one config. Secret value is masked."""
        config = self.repo.get_by_key(key)
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Config key '{key}' not found")
        return self._to_response(config)

    def get_raw_value(self, key: str) -> str | None:
        """Get plain value (for internal use by other services). Decrypts if secret."""
        config = self.repo.get_by_key(key)
        if config is None:
            return None
        if config.is_secret:
            return decrypt_value(config.value, self._enc_key, self._fallback)
        return config.value

    def set_config(
        self,
        key: str,
        value: str,
        category: str = "general",
        is_secret: bool = False,
        description: str | None = None,
    ) -> dict:
        """Create or update a config entry."""
        if is_secret and value:
            stored = encrypt_value(value, self._enc_key, self._fallback)
        else:
            stored = value
        config = SystemConfig(
            key=key,
            value=stored,
            category=category,
            is_secret=is_secret,
            description=description,
        )
        updated = self.repo.upsert(config)
        self.repo.db.commit()
        self.repo.db.refresh(updated)
        return self._to_response(updated)

    def _to_response(self, config: SystemConfig) -> dict:
        if config.is_secret and config.value:
            display = mask_secret(
                decrypt_value(config.value, self._enc_key, self._fallback) or config.value,
                visible_tail=4,
            )
        else:
            display = config.value
        return {
            "key": config.key,
            "value": display,
            "value_set": bool(config.value),
            "category": config.category,
            "is_secret": config.is_secret,
            "description": config.description,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }
