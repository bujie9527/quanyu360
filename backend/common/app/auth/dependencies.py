"""FastAPI dependencies for tenant context from JWT."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from common.app.auth.jwt import TokenClaims


@dataclass
class TenantContext:
    tenant_id: UUID
    user_id: UUID
    tenant_slug: str
    email: str
    role: str


def get_token_claims(request: Request) -> TokenClaims | None:
    return getattr(request.state, "token_claims", None)


def get_tenant_context(request: Request) -> TenantContext | None:
    claims = get_token_claims(request)
    if claims is None:
        return None
    return TenantContext(
        tenant_id=claims.tenant_id,
        user_id=claims.sub,
        tenant_slug=claims.tenant_slug,
        email=claims.email,
        role=claims.role,
    )


def require_tenant_context(
    request: Request,
    *,
    auth_required: bool = True,
) -> TenantContext:
    """Dependency that returns tenant context from JWT. When auth_required, raises 401 if no token."""
    ctx = get_tenant_context(request)
    if ctx is not None:
        return ctx
    if auth_required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token.",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No tenant context. Login required.",
    )
