"""RBAC middleware: enriches request with effective permissions from UserRoleAssignment.
Optional - only runs when RBAC tables and session are available."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RBACEnrichmentMiddleware(BaseHTTPMiddleware):
    """Adds request.state.effective_permissions (set of "resource:action" slugs).
    Requires request.state.token_claims to be set (from OptionalJWTMiddleware).
    Does not block requests - only enriches. Use require_permission dependency for enforcement."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.effective_permissions = set()
        claims = getattr(request.state, "token_claims", None)
        if claims is None:
            return await call_next(request)
        # Permissions would be loaded from DB here (user -> role_assignments -> role -> permissions)
        # For now, derive from JWT role for backward compat
        role = (getattr(claims, "role", None) or "").lower()
        if role in ("admin", "platform_admin", "tenant_admin"):
            request.state.effective_permissions = {"*:*"}  # All permissions
        elif role == "manager":
            request.state.effective_permissions = {
                "projects:*", "agents:*", "tasks:*", "workflows:*", "tenants:read"
            }
        elif role == "operator":
            request.state.effective_permissions = {
                "projects:read", "projects:update", "agents:*", "tasks:*", "workflows:*"
            }
        return await call_next(request)


def has_permission(request: Request, resource: str, action: str) -> bool:
    """Check if request has the given permission (from middleware-enriched state)."""
    perms = getattr(request.state, "effective_permissions", None) or set()
    if "*:*" in perms:
        return True
    if f"{resource}:*" in perms or f"{resource}:{action}" in perms:
        return True
    return False
