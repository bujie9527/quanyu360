"""Quotas proxy - tenant-facing quotas from admin-service."""
from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.config import settings
from app.dependencies import get_tenant_context_dep
from common.app.auth import TenantContext

router = APIRouter(prefix="/projects", tags=["quotas"])


@router.get("/quotas")
def get_tenant_quotas(
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> dict:
    """Get tenant quotas (proxies to admin-service). Requires tenant auth."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    if not settings.admin_service_url:
        return {
            "tenant_id": str(ctx.tenant_id),
            "quotas": {
                "wordpress_sites_per_month": {"current": 0, "limit": 0, "allowed": True},
            },
        }
    try:
        url = f"{settings.admin_service_url.rstrip('/')}/admin/quotas"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params={"tenant_id": str(ctx.tenant_id)})
            if resp.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Quotas service returned {resp.status_code}",
                )
            return resp.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch quotas: {e}",
        ) from e
