"""Platform domain management service."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from common.app.models import PlatformDomain
from common.app.models import PlatformDomainStatus

from app.repositories.platform_domain_repository import PlatformDomainRepository


class PlatformDomainService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PlatformDomainRepository(db)

    def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PlatformDomain], int]:
        return self.repo.list(status=status, limit=limit, offset=offset)

    def get(self, domain_id: UUID) -> PlatformDomain | None:
        return self.repo.get(domain_id)

    def create(
        self,
        domain: str,
        api_base_url: str,
        server_id: UUID | None = None,
        ssl_enabled: bool = True,
        status: str = "available",
    ) -> PlatformDomain:
        try:
            status_enum = PlatformDomainStatus(status)
        except ValueError:
            status_enum = PlatformDomainStatus.available
        pd = PlatformDomain(
            domain=domain,
            api_base_url=api_base_url,
            server_id=server_id,
            ssl_enabled=ssl_enabled,
            status=status_enum,
        )
        self.db.add(pd)
        self.db.flush()
        return pd

    def update(
        self,
        domain_id: UUID,
        domain: str | None = None,
        api_base_url: str | None = None,
        server_id: UUID | None = None,
        ssl_enabled: bool | None = None,
        status: str | None = None,
    ) -> PlatformDomain | None:
        pd = self.repo.get(domain_id)
        if pd is None:
            return None
        if domain is not None:
            pd.domain = domain
        if api_base_url is not None:
            pd.api_base_url = api_base_url
        pd.server_id = server_id
        if ssl_enabled is not None:
            pd.ssl_enabled = ssl_enabled
        if status is not None:
            try:
                pd.status = PlatformDomainStatus(status)
            except ValueError:
                pass
        self.repo.db.flush()
        return pd

    def delete(self, domain_id: UUID) -> bool:
        pd = self.repo.get(domain_id)
        if pd is None:
            return False
        self.repo.db.delete(pd)
        self.repo.db.flush()
        return True
