from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field
from pydantic import field_validator

from common.app.models import UserRole


class RegisterRequest(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=120)
    tenant_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.operator

    @field_validator("tenant_slug")
    @classmethod
    def normalize_tenant_slug(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_upper = any(char.isupper() for char in value)
        has_lower = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must include uppercase, lowercase, and numeric characters.")
        return value


class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("tenant_slug")
    @classmethod
    def normalize_tenant_slug(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    status: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class AuthenticatedUserResponse(UserResponse):
    tenant_slug: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUserResponse


class RegisterResponse(BaseModel):
    user: AuthenticatedUserResponse
    tenant_created: bool


class TokenClaims(BaseModel):
    sub: UUID
    tenant_id: UUID
    tenant_slug: str
    email: EmailStr
    role: UserRole
    iss: str
    aud: str
    exp: int
    iat: int
