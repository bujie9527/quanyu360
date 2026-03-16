from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session

from app.config import session_factory
from common.app.auth import get_tenant_context
from app.repositories import ScheduleRepository
from app.repositories import TaskRunRepository
from app.repositories import TaskTemplateRepository
from app.repositories import WorkflowRepository
from app.services import ScheduleService
from app.services import WorkflowService
from common.app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_workflow_service(db: Session = Depends(get_db_session)) -> WorkflowService:
    return WorkflowService(WorkflowRepository(db), TaskRunRepository(db))


def get_tenant_id_or_none(request: Request) -> UUID | None:
    """Get tenant_id from JWT or X-Tenant-Id header."""
    ctx = get_tenant_context(request)
    if ctx is not None:
        return ctx.tenant_id
    raw = request.headers.get("X-Tenant-Id")
    if raw:
        try:
            return UUID(raw)
        except ValueError:
            pass
    return None


def get_schedule_service(
    db: Session = Depends(get_db_session),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> ScheduleService:
    return ScheduleService(
        ScheduleRepository(db),
        TaskTemplateRepository(db),
        workflow_service.execute_workflow,
    )
