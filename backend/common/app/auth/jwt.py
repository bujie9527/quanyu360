"""Unified JWT validation for backend services."""

from __future__ import annotations

from uuid import UUID

from jose import JWTError
from jose import jwt
from pydantic import BaseModel
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class TokenClaims(BaseModel):
    """Standard JWT claims emitted by auth-service."""

    sub: UUID
    tenant_id: UUID
    tenant_slug: str
    email: str
    role: str
    iss: str
    aud: str
    exp: int
    iat: int

    @field_validator("sub", "tenant_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: UUID | str) -> UUID:
        return v if isinstance(v, UUID) else UUID(str(v))


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    jwt_secret_key: str = "unsafe-development-secret"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "ai-workforce-platform"
    jwt_audience: str = "ai-workforce-platform-users"


def _get_jwt_settings() -> JWTSettings:
    return JWTSettings()


def validate_token(token: str) -> TokenClaims:
    """Decode and validate JWT; raises JWTError on failure."""
    settings = _get_jwt_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    return TokenClaims.model_validate(payload)


def try_decode_token(token: str) -> TokenClaims | None:
    """Attempt to decode JWT; returns None on any error."""
    try:
        return validate_token(token)
    except JWTError:
        return None
