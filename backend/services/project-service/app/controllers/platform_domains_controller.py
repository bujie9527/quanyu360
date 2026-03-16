"""Platform domains - tenant-visible available domains."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies import get_db_session
from app.dependencies import get_tenant_context_dep
from common.app.auth import TenantContext
from common.app.models import PlatformDomainStatus
from sqlalchemy.orm import Session

router = APIRouter()


def _get_repo(db: Session = Depends(get_db_session)):
    from app.repositories.platform_domain_repository import PlatformDomainRepository

    return PlatformDomainRepository(db)


@router.get("/projects/platform_domains/available")
def list_available_platform_domains(
    repo=Depends(_get_repo),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> dict:
    """Return platform domains with status=available. Requires tenant auth."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    domains = repo.get_available()
    return {
        "items": [
            {
                "id": str(d.id),
                "domain": d.domain,
                "api_base_url": d.api_base_url,
                "ssl_enabled": d.ssl_enabled,
            }
            for d in domains
        ],
    }
