from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session

from app.config import session_factory
from app.config import settings
from app.repositories import AgentTeamRepository
from app.repositories import AssetRepository
from app.repositories import ProjectRepository
from app.services import AgentTeamService
from app.services import AssetService
from app.services import ProjectService
from common.app.auth import TenantContext
from common.app.auth import require_tenant_context
from common.app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_project_service(db: Session = Depends(get_db_session)) -> ProjectService:
    return ProjectService(ProjectRepository(db))


def get_asset_service(db: Session = Depends(get_db_session)) -> AssetService:
    return AssetService(AssetRepository(db))


def get_agent_team_service(db: Session = Depends(get_db_session)) -> AgentTeamService:
    return AgentTeamService(AgentTeamRepository(db))


def get_tenant_context_dep(request: Request) -> TenantContext | None:
    """Return tenant context from JWT when present. When AUTH_REQUIRED=true, raises 401 if absent."""
    from common.app.auth import get_tenant_context

    ctx = get_tenant_context(request)
    if ctx is not None:
        return ctx
    if settings.auth_required:
        return require_tenant_context(request, auth_required=True)
    return None


def get_tenant_context_required(request: Request) -> TenantContext:
    """Return tenant context from JWT. Raises 401 if absent."""
    return require_tenant_context(request, auth_required=True)
