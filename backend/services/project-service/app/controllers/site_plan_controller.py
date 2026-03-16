"""Site plan endpoints for matrix-site projects."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.dependencies import get_db_session
from app.dependencies import get_tenant_context_dep
from app.schemas.site_plan_schemas import SitePlanApproveRequest
from app.schemas.site_plan_schemas import SitePlanCreateRequest
from app.schemas.site_plan_schemas import SitePlanItemResponse
from app.schemas.site_plan_schemas import SitePlanListResponse
from app.schemas.site_plan_schemas import SitePlanResponse
from common.app.auth import TenantContext
from common.app.models import Project
from common.app.models import SitePlan
from common.app.models import SitePlanItem
from common.app.models import SitePlanStatus

router = APIRouter(prefix="/projects", tags=["site-plans"])


def _ensure_project_access(
    db: Session,
    project_id: UUID,
    ctx: TenantContext | None,
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if ctx and project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _to_item(item: SitePlanItem) -> SitePlanItemResponse:
    return SitePlanItemResponse(
        id=item.id,
        site_name=item.site_name,
        site_theme=item.site_theme,
        target_audience=item.target_audience,
        content_direction=item.content_direction,
        seo_keywords=item.seo_keywords or [],
        site_structure=item.site_structure or {},
        wordpress_site_id=item.wordpress_site_id,
        status=item.status.value,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_plan(plan: SitePlan) -> SitePlanResponse:
    return SitePlanResponse(
        id=plan.id,
        project_id=plan.project_id,
        status=plan.status.value,
        agent_input=plan.agent_input or {},
        agent_output=plan.agent_output or {},
        approved_at=plan.approved_at,
        approved_by=plan.approved_by,
        items=[_to_item(item) for item in plan.items],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.get("/{project_id}/site-plans", response_model=SitePlanListResponse)
def list_site_plans(
    project_id: UUID,
    status_filter: SitePlanStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> SitePlanListResponse:
    _ensure_project_access(db, project_id, ctx)

    stmt = (
        select(SitePlan)
        .where(SitePlan.project_id == project_id)
        .options(selectinload(SitePlan.items))
        .order_by(SitePlan.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter is not None:
        stmt = stmt.where(SitePlan.status == status_filter)
    items = list(db.scalars(stmt).all())

    count_stmt = select(func.count(SitePlan.id)).where(SitePlan.project_id == project_id)
    if status_filter is not None:
        count_stmt = count_stmt.where(SitePlan.status == status_filter)
    total = db.scalar(count_stmt) or 0
    return SitePlanListResponse(items=[_to_plan(p) for p in items], total=total)


@router.post("/{project_id}/site-plans", response_model=SitePlanResponse, status_code=status.HTTP_201_CREATED)
def create_site_plan(
    project_id: UUID,
    payload: SitePlanCreateRequest,
    db: Session = Depends(get_db_session),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> SitePlanResponse:
    _ensure_project_access(db, project_id, ctx)

    plan = SitePlan(
        project_id=project_id,
        status=SitePlanStatus.draft,
        agent_input=payload.agent_input or {},
        agent_output=payload.agent_output or {},
    )
    db.add(plan)
    db.flush()

    for item in payload.items:
        db.add(
            SitePlanItem(
                site_plan_id=plan.id,
                site_name=item.site_name,
                site_theme=item.site_theme,
                target_audience=item.target_audience,
                content_direction=item.content_direction,
                seo_keywords=item.seo_keywords,
                site_structure=item.site_structure,
            )
        )
    db.commit()
    db.refresh(plan)
    refreshed = db.scalar(select(SitePlan).where(SitePlan.id == plan.id).options(selectinload(SitePlan.items)))
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reload SitePlan after create.")
    return _to_plan(refreshed)


@router.patch("/site-plans/{plan_id}/approve", response_model=SitePlanResponse)
def approve_site_plan(
    plan_id: UUID,
    payload: SitePlanApproveRequest,
    db: Session = Depends(get_db_session),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> SitePlanResponse:
    plan = db.scalar(select(SitePlan).where(SitePlan.id == plan_id).options(selectinload(SitePlan.items)))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SitePlan not found.")
    _ensure_project_access(db, plan.project_id, ctx)

    plan.status = SitePlanStatus.approved
    plan.approved_at = datetime.now(timezone.utc)
    plan.approved_by = payload.approved_by or (ctx.user_id if ctx else None)
    db.commit()
    db.refresh(plan)
    refreshed = db.scalar(select(SitePlan).where(SitePlan.id == plan.id).options(selectinload(SitePlan.items)))
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reload SitePlan after approve.")
    return _to_plan(refreshed)
