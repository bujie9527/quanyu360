"""System config data access."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import SystemConfig


class SystemConfigRepository:
    """Handles database access for system configuration."""

    def __init__(self, db: Session):
        self.db = db

    def list_all(self, category: str | None = None) -> list[SystemConfig]:
        stmt = select(SystemConfig).order_by(SystemConfig.category.asc(), SystemConfig.key.asc())
        if category:
            stmt = stmt.where(SystemConfig.category == category)
        return list(self.db.scalars(stmt).all())

    def get_by_key(self, key: str) -> SystemConfig | None:
        return self.db.scalar(select(SystemConfig).where(SystemConfig.key == key))

    def upsert(self, config: SystemConfig) -> SystemConfig:
        existing = self.get_by_key(config.key)
        if existing:
            existing.value = config.value
            existing.category = config.category
            existing.is_secret = config.is_secret
            existing.description = config.description
            self.db.flush()
            self.db.refresh(existing)
            return existing
        self.db.add(config)
        self.db.flush()
        self.db.refresh(config)
        return config
