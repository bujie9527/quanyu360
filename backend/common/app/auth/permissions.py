"""Permission checking for RBAC."""
from __future__ import annotations

from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from common.app.auth.dependencies import TenantContext
from common.app.auth.dependencies import get_tenant_context
from common.app.auth.rbac_middleware import has_permission


def require_permission(resource: str, action: str):
    """Dependency factory that requires the caller to have the given permission.
    Uses request.state.effective_permissions (set by RBACEnrichmentMiddleware).
    Falls back to JWT role (admin/manager) for backward compatibility.
    """

    def _check(request: Request) -> TenantContext:
        ctx = get_tenant_context(request)
        if ctx is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        if has_permission(request, resource, action):
            return ctx
        role_lower = (ctx.role or "").lower()
        if role_lower in ("platform_admin", "tenant_admin", "admin", "manager"):
            return ctx
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {resource}:{action}",
        )

    return _check


def require_platform_admin(ctx: TenantContext | None = None):
    """Check that the user has platform_admin role."""
    if ctx is None:
        return
    role_lower = (ctx.role or "").lower()
    if role_lower == "platform_admin":
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Platform admin required.",
    )
