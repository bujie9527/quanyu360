"""WordPress site data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import Project
from common.app.models import WordPressSite


class WordPressSiteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_tenant(self, tenant_id: UUID, project_id: UUID | None = None) -> list[WordPressSite]:
        stmt = select(WordPressSite).where(WordPressSite.tenant_id == tenant_id)
        if project_id is not None:
            stmt = stmt.where(WordPressSite.project_id == project_id)
        stmt = stmt.order_by(WordPressSite.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get(self, site_id: UUID, tenant_id: UUID | None = None) -> WordPressSite | None:
        stmt = select(WordPressSite).where(WordPressSite.id == site_id)
        if tenant_id is not None:
            stmt = stmt.where(WordPressSite.tenant_id == tenant_id)
        return self.db.scalar(stmt)

    def add(self, site: WordPressSite) -> None:
        self.db.add(site)
        self.db.flush()

    def delete(self, site: WordPressSite) -> None:
        self.db.delete(site)
