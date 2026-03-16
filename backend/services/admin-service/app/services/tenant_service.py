"""Tenant business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import TenantRepository
from app.schemas.tenant_schemas import TenantCreateRequest
from app.schemas.tenant_schemas import TenantUpdateRequest
from common.app.models import Tenant
from common.app.models import TenantStatus


class TenantService:
    """Orchestrates tenant business logic."""

    def __init__(self, repo: TenantRepository):
        self.repo = repo

    def list_tenants(
        self,
        status_filter: TenantStatus | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Tenant], int]:
        return self.repo.list(
            status_filter=status_filter,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = self.repo.get(tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found.",
            )
        return tenant

    def create_tenant(self, payload: TenantCreateRequest) -> Tenant:
        existing = self.repo.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with slug '{payload.slug}' already exists.",
            )
        tenant = Tenant(
            name=payload.name,
            slug=payload.slug.lower().replace(" ", "-"),
            status=payload.status,
            plan_name=payload.plan_name,
            settings=payload.settings,
        )
        self.repo.add(tenant)
        self.repo.db.commit()
        self.repo.db.refresh(tenant)
        return tenant

    def update_tenant(self, tenant_id: UUID, payload: TenantUpdateRequest) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        if payload.name is not None:
            tenant.name = payload.name
        if payload.slug is not None:
            existing = self.repo.get_by_slug(payload.slug)
            if existing is not None and existing.id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tenant with slug '{payload.slug}' already exists.",
                )
            tenant.slug = payload.slug
        if payload.status is not None:
            tenant.status = payload.status
        if payload.plan_name is not None:
            tenant.plan_name = payload.plan_name
        if payload.settings is not None:
            tenant.settings = payload.settings
        self.repo.db.commit()
        self.repo.db.refresh(tenant)
        return tenant

    def delete_tenant(self, tenant_id: UUID) -> None:
        tenant = self.get_tenant(tenant_id)
        self.repo.delete(tenant)
        self.repo.db.commit()
