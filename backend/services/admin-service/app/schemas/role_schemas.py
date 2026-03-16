"""Role request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class RoleCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.lower().replace(" ", "_")


class RoleUpdateRequest(BaseModel):
    slug: str | None = Field(default=None, min_length=2, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.lower().replace(" ", "_") if value else value


class RoleSummaryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class RoleDetailResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleSummaryResponse]
    total: int


class UserRoleAssignItem(BaseModel):
    role_id: UUID
    tenant_id: UUID | None = None  # None = platform scope


class UserRolesAssignRequest(BaseModel):
    roles: list[UserRoleAssignItem] = Field(min_length=1)


class UserRoleAssignmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    role_id: UUID
    tenant_id: UUID | None
    created_at: datetime
