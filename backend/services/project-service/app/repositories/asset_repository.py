"""Asset data access layer."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from common.app.models import Asset
from common.app.models import Project


class AssetRepository:
    """Handles database access for assets."""

    def __init__(self, db: Session):
        self.db = db

    def get_project(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def add_asset(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset
