"""Platform domain admin HTTP endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.platform_domain_schemas import PlatformDomainCreateRequest
from app.schemas.platform_domain_schemas import PlatformDomainListResponse
from app.schemas.platform_domain_schemas import PlatformDomainResponse
from app.schemas.platform_domain_schemas import PlatformDomainUpdateRequest
from app.services.platform_domain_service import PlatformDomainService

router = APIRouter(prefix="/admin/platform_domains", tags=["platform-domains"])


def _get_service(db: Session = Depends(get_db_session)) -> PlatformDomainService:
    return PlatformDomainService(db)


def _to_response(pd) -> PlatformDomainResponse:
    return PlatformDomainResponse(
        id=pd.id,
        domain=pd.domain,
        api_base_url=pd.api_base_url,
        server_id=pd.server_id,
        ssl_enabled=pd.ssl_enabled,
        status=pd.status.value,
        created_at=pd.created_at,
        updated_at=pd.updated_at,
    )


@router.get("", response_model=PlatformDomainListResponse)
def list_platform_domains(
    status: str | None = Query(default=None, pattern="^(available|assigned|inactive)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: PlatformDomainService = Depends(_get_service),
) -> PlatformDomainListResponse:
    """List platform domains with optional status filter."""
    items, total = service.list(status=status, limit=limit, offset=offset)
    return PlatformDomainListResponse(
        items=[_to_response(p) for p in items],
        total=total,
    )


@router.post("", response_model=PlatformDomainResponse, status_code=status.HTTP_201_CREATED)
def create_platform_domain(
    payload: PlatformDomainCreateRequest,
    service: PlatformDomainService = Depends(_get_service),
) -> PlatformDomainResponse:
    """Create a platform domain."""
    pd = service.create(
        domain=payload.domain,
        api_base_url=payload.api_base_url,
        server_id=payload.server_id,
        ssl_enabled=payload.ssl_enabled,
        status=payload.status,
    )
    service.db.commit()
    return _to_response(pd)


@router.get("/{domain_id}", response_model=PlatformDomainResponse)
def get_platform_domain(
    domain_id: UUID,
    service: PlatformDomainService = Depends(_get_service),
) -> PlatformDomainResponse:
    """Get platform domain by ID."""
    pd = service.get(domain_id)
    if pd is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform domain not found")
    return _to_response(pd)


@router.patch("/{domain_id}", response_model=PlatformDomainResponse)
def update_platform_domain(
    domain_id: UUID,
    payload: PlatformDomainUpdateRequest,
    service: PlatformDomainService = Depends(_get_service),
) -> PlatformDomainResponse:
    """Update platform domain."""
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    pd = service.update(
        domain_id,
        domain=updates.get("domain"),
        api_base_url=updates.get("api_base_url"),
        server_id=updates.get("server_id"),
        ssl_enabled=updates.get("ssl_enabled"),
        status=updates.get("status"),
    )
    if pd is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform domain not found")
    service.db.commit()
    return _to_response(pd)


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_domain(
    domain_id: UUID,
    service: PlatformDomainService = Depends(_get_service),
) -> None:
    """Delete platform domain."""
    if not service.delete(domain_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform domain not found")
    service.db.commit()
