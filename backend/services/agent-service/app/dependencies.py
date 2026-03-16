from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session

from app.config import session_factory
from app.repositories import AgentRepository
from app.repositories import AgentInstanceRepository
from app.repositories import AgentTemplateRepository
from app.services import AgentService
from app.services import AgentInstanceService
from app.services import AgentTemplateService
from common.app.auth.dependencies import get_tenant_context
from common.app.auth.permissions import require_platform_admin as _check_platform_admin
from common.app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_agent_service(db: Session = Depends(get_db_session)) -> AgentService:
    return AgentService(AgentRepository(db))


def get_agent_template_service(db: Session = Depends(get_db_session)) -> AgentTemplateService:
    return AgentTemplateService(AgentTemplateRepository(db))


def get_agent_instance_service(db: Session = Depends(get_db_session)) -> AgentInstanceService:
    return AgentInstanceService(AgentInstanceRepository(db))


def require_platform_admin(request: Request) -> None:
    """Raises 401 if unauthenticated, 403 if not platform admin. Call in endpoints that need platform admin."""
    ctx = get_tenant_context(request)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token.",
        )
    require_platform_admin(ctx)


def _check_platform_admin(ctx) -> None:
    from common.app.auth.permissions import require_platform_admin as _check
    _check(ctx)
