"""JWT validation middleware."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings
from jose import JWTError, jwt


def _is_public_path(path: str) -> bool:
    settings = get_settings()
    path_normalized = path.rstrip("/") or "/"
    for public in settings.public_paths:
        p = public.rstrip("/") or "/"
        if path_normalized == p or path_normalized.startswith(p + "/"):
            return True
    return False


def validate_jwt(request: Request) -> tuple[bool, str | None]:
    """
    Validate JWT from Authorization header.
    Returns (is_valid, error_message).
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"
    token = auth[7:]
    settings = get_settings()
    try:
        jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        return True, None
    except JWTError as e:
        return False, str(e)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.jwt_enabled:
            return await call_next(request)
        path = request.url.path
        if _is_public_path(path):
            return await call_next(request)
        valid, err = validate_jwt(request)
        if not valid:
            return JSONResponse(
                status_code=401,
                content={"detail": err or "Unauthorized"},
            )
        return await call_next(request)
