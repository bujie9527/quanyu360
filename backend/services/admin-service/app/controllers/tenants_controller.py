"""Tenant admin HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from app.dependencies import get_tenant_service
from app.schemas.tenant_schemas import TenantCreateRequest
from app.schemas.tenant_schemas import TenantDetailResponse
from app.schemas.tenant_schemas import TenantUpdateRequest
from app.schemas.tenant_schemas import TenantListResponse
from app.schemas.tenant_schemas import TenantSummaryResponse
from app.services import TenantService
from common.app.models import Tenant
from common.app.models import TenantStatus

router = APIRouter(prefix="/admin", tags=["tenants"])


def _to_summary(tenant: Tenant) -> TenantSummaryResponse:
    return TenantSummaryResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status.value,
        plan_name=tenant.plan_name,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


def _to_detail(tenant: Tenant) -> TenantDetailResponse:
    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status.value,
        plan_name=tenant.plan_name,
        settings=tenant.settings or {},
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.post("/tenants", response_model=TenantDetailResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreateRequest,
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantDetailResponse:
    tenant = tenant_service.create_tenant(payload)
    return _to_detail(tenant)


@router.get("/tenants", response_model=TenantListResponse)
def list_tenants(
    status_filter: TenantStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantListResponse:
    items, total = tenant_service.list_tenants(
        status_filter=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return TenantListResponse(
        items=[_to_summary(t) for t in items],
        total=total,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantDetailResponse)
def get_tenant(
    tenant_id: UUID,
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantDetailResponse:
    tenant = tenant_service.get_tenant(tenant_id)
    return _to_detail(tenant)


@router.put("/tenants/{tenant_id}", response_model=TenantDetailResponse)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdateRequest,
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantDetailResponse:
    tenant = tenant_service.update_tenant(tenant_id, payload)
    return _to_detail(tenant)


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: UUID,
    tenant_service: TenantService = Depends(get_tenant_service),
) -> None:
    tenant_service.delete_tenant(tenant_id)
