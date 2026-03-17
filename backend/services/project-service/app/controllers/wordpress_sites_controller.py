"""WordPress site HTTP endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from app.dependencies import get_db_session
from app.dependencies import get_tenant_context_dep
from app.schemas.wordpress_site_schemas import WordPressSiteCreateRequest
from app.schemas.wordpress_site_schemas import WordPressSiteCredentialsUpdateRequest
from app.schemas.wordpress_site_schemas import WordPressSiteDetailResponse
from app.schemas.wordpress_site_schemas import WordPressSiteResponse
from app.schemas.wordpress_site_schemas import WordPressSiteTestResponse
from app.services.wordpress_site_service import WordPressSiteService
from common.app.auth import TenantContext
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sites", tags=["wordpress-sites"])


def _get_service(db: Session = Depends(get_db_session)) -> WordPressSiteService:
    from app.repositories import ProjectRepository
    from app.repositories.wordpress_site_repository import WordPressSiteRepository

    return WordPressSiteService(
        db=db,
        project_repo=ProjectRepository(db),
        site_repo=WordPressSiteRepository(db),
    )


def _to_response(site) -> WordPressSiteResponse:
    return WordPressSiteResponse(
        id=site.id,
        tenant_id=site.tenant_id,
        project_id=site.project_id,
        server_id=site.server_id,
        install_task_run_id=site.install_task_run_id,
        name=site.name,
        domain=site.domain,
        api_url=site.api_url,
        username=site.username,
        status=site.status.value,
        created_at=site.created_at,
    )


def _to_detail_response(site) -> WordPressSiteDetailResponse:
    return WordPressSiteDetailResponse(**_to_response(site).model_dump())


@router.post("", response_model=WordPressSiteDetailResponse, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: WordPressSiteCreateRequest,
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> WordPressSiteDetailResponse:
    """创建 WordPress 站点."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    site = service.create_site(
        tenant_id=ctx.tenant_id,
        project_id=payload.project_id,
        name=payload.name,
        domain=payload.domain,
        api_url=payload.api_url,
        username=payload.username,
        app_password=payload.app_password,
    )
    return _to_detail_response(site)


@router.get("", response_model=list[WordPressSiteResponse])
def list_sites(
    project_id: UUID | None = Query(default=None),
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> list[WordPressSiteResponse]:
    """获取租户下所有 WordPress 站点."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    sites = service.list_sites(tenant_id=ctx.tenant_id, project_id=project_id)
    return [_to_response(s) for s in sites]


@router.get("/{site_id}", response_model=WordPressSiteDetailResponse)
def get_site(
    site_id: UUID,
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> WordPressSiteDetailResponse:
    """获取站点详情."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    site = service.get_site(site_id, ctx.tenant_id)
    return _to_detail_response(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: UUID,
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> None:
    """删除站点."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    service.delete_site(site_id, ctx.tenant_id)


@router.get("/{site_id}/credentials")
def get_site_credentials(
    site_id: UUID,
    tenant_id: UUID | None = Query(default=None, description="Tenant ID（内部调用时必填）"),
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> dict:
    """Internal: 获取站点凭证供工具使用。需 tenant_id 或 JWT 租户上下文。"""
    effective_tenant = ctx.tenant_id if ctx else tenant_id
    if not effective_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="需要 tenant_id 查询参数或 JWT 租户上下文")
    site = service.get_site(site_id, effective_tenant)
    return {"api_url": site.api_url, "username": site.username, "app_password": site.app_password}


@router.patch("/{site_id}/credentials", response_model=WordPressSiteDetailResponse)
def update_site_credentials(
    site_id: UUID,
    payload: WordPressSiteCredentialsUpdateRequest,
    x_internal_key: str | None = Header(default=None),
    service: WordPressSiteService = Depends(_get_service),
) -> WordPressSiteDetailResponse:
    """Internal: 更新站点凭证（用于 WP-CLI 安装完成回写）。需 X-Internal-Key 头。"""
    from app.config import settings
    from common.app.models import WordPressSiteStatus

    if settings.internal_api_key and x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal API key.")

    site = service.update_credentials_internal(
        site_id=site_id,
        username=payload.username,
        app_password=payload.app_password,
        status=WordPressSiteStatus(payload.status),
    )
    return _to_detail_response(site)


@router.post("/{site_id}/test", response_model=WordPressSiteTestResponse)
def test_site_connection(
    site_id: UUID,
    service: WordPressSiteService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> WordPressSiteTestResponse:
    """测试 WordPress REST API 连接."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    result = service.test_connection(site_id, ctx.tenant_id)
    return WordPressSiteTestResponse(
        success=result.success,
        message=result.message,
        site_name=result.site_name,
        wp_version=result.wp_version,
    )
