"""Centralized audit logging helpers."""
from __future__ import annotations

from uuid import UUID

from common.app.models import AuditAction
from common.app.models import AuditLog


def log_audit(
    session,
    *,
    tenant_id: UUID,
    action: AuditAction,
    entity_type: str,
    entity_id: UUID | None = None,
    project_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    correlation_id: str | None = None,
    payload: dict | None = None,
) -> AuditLog:
    """Write an audit log entry."""
    entry = AuditLog(
        tenant_id=tenant_id,
        project_id=project_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=correlation_id,
        payload=payload or {},
    )
    session.add(entry)
    return entry
