"""Platform domain data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import PlatformDomain
from common.app.models import PlatformDomainStatus


class PlatformDomainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PlatformDomain], int]:
        stmt = select(PlatformDomain)
        count_stmt = select(func.count(PlatformDomain.id))
        if status is not None:
            try:
                status_enum = PlatformDomainStatus(status)
                stmt = stmt.where(PlatformDomain.status == status_enum)
                count_stmt = count_stmt.where(PlatformDomain.status == status_enum)
            except ValueError:
                pass
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(PlatformDomain.created_at.desc()).offset(offset).limit(limit))
        )
        return items, total

    def get(self, domain_id: UUID) -> PlatformDomain | None:
        return self.db.get(PlatformDomain, domain_id)

    def get_by_ids(self, domain_ids: list[UUID], status: PlatformDomainStatus | None = None) -> list[PlatformDomain]:
        if not domain_ids:
            return []
        stmt = select(PlatformDomain).where(PlatformDomain.id.in_(domain_ids))
        if status is not None:
            stmt = stmt.where(PlatformDomain.status == status)
        return list(self.db.scalars(stmt))

    def get_available(self) -> list[PlatformDomain]:
        stmt = select(PlatformDomain).where(PlatformDomain.status == PlatformDomainStatus.available)
        return list(self.db.scalars(stmt.order_by(PlatformDomain.domain)))
