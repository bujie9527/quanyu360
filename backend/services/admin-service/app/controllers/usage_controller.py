"""Usage tracking HTTP endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.usage_schemas import QuotaListResponse
from app.schemas.usage_schemas import QuotaUpdateRequest
from app.schemas.usage_schemas import UsageIngestRequest
from app.schemas.usage_schemas import UsageListResponse
from app.schemas.usage_schemas import UsageLogResponse
from app.schemas.usage_schemas import UsageSummaryResponse
from app.services.quota_service import QuotaService
from app.services.usage_tracker import UsageTracker

router = APIRouter(prefix="/admin", tags=["usage"])
logger = structlog.get_logger("usage_controller")


@router.get("/usage/summary", response_model=UsageSummaryResponse)
def get_usage_summary(
    tenant_id: UUID = Query(...),
    from_at: datetime | None = Query(default=None),
    to_at: datetime | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> UsageSummaryResponse:
    """Get aggregated usage for a tenant. Optional date range filter."""
    tracker = UsageTracker(db)
    summary = tracker.summary(tenant_id=tenant_id, from_at=from_at, to_at=to_at)
    return UsageSummaryResponse(
        tenant_id=summary.tenant_id,
        llm_tokens_total=summary.llm_tokens_total,
        llm_prompt_tokens=summary.llm_prompt_tokens,
        llm_completion_tokens=summary.llm_completion_tokens,
        workflow_runs=summary.workflow_runs,
        tool_executions=summary.tool_executions,
        from_at=summary.from_at,
        to_at=summary.to_at,
    )


@router.get("/usage", response_model=UsageListResponse)
def list_usage_logs(
    tenant_id: UUID | None = Query(default=None),
    from_at: datetime | None = Query(default=None),
    to_at: datetime | None = Query(default=None),
    usage_type: str | None = Query(default=None, pattern="^(llm_tokens|workflow_run|tool_execution)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> UsageListResponse:
    """List usage logs with optional filters."""
    tracker = UsageTracker(db)
    items, total = tracker.list_logs(
        tenant_id=tenant_id,
        from_at=from_at,
        to_at=to_at,
        usage_type=usage_type,
        limit=limit,
        offset=offset,
    )
    return UsageListResponse(
        items=[
            UsageLogResponse(
                id=u.id,
                tenant_id=u.tenant_id,
                usage_type=u.usage_type.value,
                project_id=u.project_id,
                prompt_tokens=u.prompt_tokens,
                completion_tokens=u.completion_tokens,
                quantity=u.quantity,
                created_at=u.created_at,
            )
            for u in items
        ],
        total=total,
    )


@router.get("/quotas/check")
def check_quota(
    tenant_id: UUID = Query(...),
    resource: str = Query(..., pattern="^(tasks_per_month|llm_requests_per_month|workflows_per_month|wordpress_sites_per_month)$"),
    db: Session = Depends(get_db_session),
) -> dict:
    """Check if tenant has quota for resource. Returns allowed, current, limit."""
    service = QuotaService(db)
    result = service.check(tenant_id=tenant_id, resource=resource)
    return {
        "allowed": result.allowed,
        "current": result.current,
        "limit": result.limit,
        "resource": result.resource,
        "message": result.message,
    }


@router.get("/quotas", response_model=QuotaListResponse)
def list_quotas(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db_session),
) -> QuotaListResponse:
    """Get all quota resources (current, limit, allowed) for a tenant."""
    service = QuotaService(db)
    data = service.list_quotas(tenant_id)
    return QuotaListResponse(**data)


@router.post("/usage/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_usage(
    payload: UsageIngestRequest,
    db: Session = Depends(get_db_session),
) -> None:
    """
    Ingest usage from agent-runtime, workflow-engine.
    Fire-and-forget: on FK/IntegrityError we log and return 204.
    """
    tracker = UsageTracker(db)
    meta = {k: v for k, v in (payload.metadata or {}).items() if v is not None}
    entry = tracker.track(
        tenant_id=payload.tenant_id,
        usage_type=payload.usage_type,
        project_id=payload.project_id,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
        quantity=payload.quantity,
        metadata=meta,
    )
    if entry:
        db.commit()
    else:
        db.rollback()
        logger.warning(
            "usage_ingest_skipped",
            tenant_id=str(payload.tenant_id),
            usage_type=payload.usage_type,
        )


@router.put("/tenants/{tenant_id}/quotas")
def update_tenant_quotas(
    tenant_id: UUID,
    payload: QuotaUpdateRequest,
    db: Session = Depends(get_db_session),
) -> dict:
    """Update tenant quotas. Only provided fields are updated."""
    service = QuotaService(db)
    quotas = {}
    if payload.tasks_per_month is not None:
        quotas["tasks_per_month"] = payload.tasks_per_month
    if payload.llm_requests_per_month is not None:
        quotas["llm_requests_per_month"] = payload.llm_requests_per_month
    if payload.workflows_per_month is not None:
        quotas["workflows_per_month"] = payload.workflows_per_month
    if payload.wordpress_sites_per_month is not None:
        quotas["wordpress_sites_per_month"] = payload.wordpress_sites_per_month
    if not quotas:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one quota field required")
    try:
        service.update_quotas(tenant_id, quotas)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return service.list_quotas(tenant_id)
