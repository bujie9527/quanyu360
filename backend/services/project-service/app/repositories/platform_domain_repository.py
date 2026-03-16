"""Platform domain data access - tenant-visible available domains."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import PlatformDomain
from common.app.models import PlatformDomainStatus


class PlatformDomainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_available(self) -> list[PlatformDomain]:
        stmt = select(PlatformDomain).where(PlatformDomain.status == PlatformDomainStatus.available)
        return list(self.db.scalars(stmt.order_by(PlatformDomain.domain)))
