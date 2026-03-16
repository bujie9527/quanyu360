"""Optional JWT middleware: validates Bearer token when present, sets request.state.token_claims."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from common.app.auth.jwt import try_decode_token


class OptionalJWTMiddleware(BaseHTTPMiddleware):
    """Parse Authorization: Bearer <token> when present; set request.state.token_claims."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.token_claims = None

        auth = request.headers.get("Authorization")
        if not auth:
            return await call_next(request)

        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return await call_next(request)

        claims = try_decode_token(token)
        if claims is not None:
            request.state.token_claims = claims

        return await call_next(request)
