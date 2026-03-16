from __future__ import annotations

from collections.abc import Callable
from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import session_factory
from app.schemas import TokenClaims
from common.app.db.session import get_db
from common.app.models import User
from common.app.models import UserRole
from common.app.models import UserStatus


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_optional_token_claims(request: Request) -> TokenClaims | None:
    return getattr(request.state, "token_claims", None)


def get_token_claims(request: Request) -> TokenClaims:
    token_claims = get_optional_token_claims(request)
    if token_claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )
    return token_claims


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db_session),
) -> User | None:
    token_claims = get_optional_token_claims(request)
    if token_claims is None:
        return None

    user = db.scalar(
        select(User).where(
            User.id == token_claims.sub,
            User.tenant_id == token_claims.tenant_id,
        )
    )
    if user is None or user.status != UserStatus.active:
        return None
    return user


def get_current_user(
    token_claims: TokenClaims = Depends(get_token_claims),
    db: Session = Depends(get_db_session),
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == token_claims.sub,
            User.tenant_id == token_claims.tenant_id,
        )
    )
    if user is None or user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    allowed = set(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions.",
            )
        return current_user

    return dependency
