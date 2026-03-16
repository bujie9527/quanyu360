"""Tenant data access layer."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import Tenant
from common.app.models import TenantStatus


class TenantRepository:
    """Handles database access for tenants."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        status_filter: TenantStatus | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Tenant], int]:
        statement = select(Tenant)
        count_statement = select(func.count(Tenant.id))
        if status_filter is not None:
            statement = statement.where(Tenant.status == status_filter)
            count_statement = count_statement.where(Tenant.status == status_filter)
        if search and search.strip():
            term = f"%{search.strip()}%"
            pred = or_(Tenant.name.ilike(term), Tenant.slug.ilike(term))
            statement = statement.where(pred)
            count_statement = count_statement.where(pred)
        items = list(
            self.db.scalars(
                statement.order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, tenant_id: UUID) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return self.db.scalar(select(Tenant).where(Tenant.slug == slug.lower()))

    def add(self, tenant: Tenant) -> None:
        self.db.add(tenant)

    def delete(self, tenant: Tenant) -> None:
        self.db.delete(tenant)
