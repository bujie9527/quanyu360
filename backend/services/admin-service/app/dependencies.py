"""Admin service dependencies."""
from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.config import session_factory
from app.repositories import RoleRepository
from app.repositories import TenantRepository
from app.services import RoleService
from app.services import TenantService
from common.app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_tenant_service(db: Session = Depends(get_db_session)) -> TenantService:
    return TenantService(TenantRepository(db))


def get_role_service(db: Session = Depends(get_db_session)) -> RoleService:
    return RoleService(RoleRepository(db))
