"""Audit log repository."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import AuditLog


def list_audit_logs(
    session: Session,
    *,
    tenant_id: UUID | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    correlation_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    """List audit logs with filters. Returns (items, total)."""
    stmt = select(AuditLog)
    count_stmt = select(func.count(AuditLog.id))

    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        count_stmt = count_stmt.where(AuditLog.tenant_id == tenant_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
        count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    if correlation_id:
        stmt = stmt.where(AuditLog.correlation_id == correlation_id)
        count_stmt = count_stmt.where(AuditLog.correlation_id == correlation_id)
    if since is not None:
        stmt = stmt.where(AuditLog.created_at >= since)
        count_stmt = count_stmt.where(AuditLog.created_at >= since)
    if until is not None:
        stmt = stmt.where(AuditLog.created_at <= until)
        count_stmt = count_stmt.where(AuditLog.created_at <= until)

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    items = list(session.scalars(stmt).all())
    total = session.scalar(count_stmt) or 0
    return items, total
