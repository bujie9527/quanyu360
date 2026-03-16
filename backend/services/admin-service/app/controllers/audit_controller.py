"""Audit log HTTP endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.repositories.audit_repository import list_audit_logs
from app.schemas.audit_schemas import AuditIngestRequest
from app.schemas.audit_schemas import AuditLogResponse
from common.app.audit import log_audit
from common.app.models import AuditAction
from common.app.models import AuditLog

router = APIRouter(prefix="/admin", tags=["audit"])
logger = structlog.get_logger("audit_controller")


def _to_response(entry: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=str(entry.id),
        tenant_id=str(entry.tenant_id),
        project_id=str(entry.project_id) if entry.project_id else None,
        actor_user_id=str(entry.actor_user_id) if entry.actor_user_id else None,
        action=entry.action.value,
        entity_type=entry.entity_type,
        entity_id=str(entry.entity_id) if entry.entity_id else None,
        correlation_id=entry.correlation_id,
        created_at=entry.created_at,
        payload=entry.payload or {},
    )


@router.post("/audit/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_audit(
    payload: AuditIngestRequest,
    db: Session = Depends(get_db_session),
) -> None:
    """
    Ingest an audit log entry from internal services (agent-runtime, workflow-engine).
    No JWT required when called from internal network.
    Fire-and-forget: on FK/IntegrityError we log and return 204.
    """
    try:
        action = AuditAction(payload.action)
    except ValueError:
        action = AuditAction.execute
    try:
        log_audit(
            session=db,
            tenant_id=payload.tenant_id,
            project_id=payload.project_id,
            action=action,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            correlation_id=payload.correlation_id,
            payload=payload.payload,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning(
            "audit_ingest_integrity_error",
            entity_type=payload.entity_type,
            tenant_id=str(payload.tenant_id),
            error=str(exc),
        )


@router.get("/audit", response_model=dict)
def list_audit(
    tenant_id: UUID | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> dict:
    """List audit logs with filters. Requires admin permission."""
    items, total = list_audit_logs(
        session=db,
        tenant_id=tenant_id,
        entity_type=entity_type,
        action=action,
        correlation_id=correlation_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return {"items": [_to_response(e) for e in items], "total": total}
