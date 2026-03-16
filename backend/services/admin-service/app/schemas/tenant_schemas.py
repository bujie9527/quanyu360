"""Tenant request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from common.app.models import TenantStatus


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=120)
    status: TenantStatus = TenantStatus.active
    plan_name: str = Field(default="mvp", min_length=1, max_length=80)
    settings: dict[str, object] = Field(default_factory=dict)

    @field_validator("name", "slug")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.lower().replace(" ", "-")


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    status: TenantStatus | None = None
    plan_name: str | None = Field(default=None, min_length=1, max_length=80)
    settings: dict[str, object] | None = None

    @field_validator("name", "slug")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.lower().replace(" ", "-") if value else value


class TenantSummaryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    plan_name: str
    created_at: datetime
    updated_at: datetime


class TenantDetailResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    plan_name: str
    settings: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantSummaryResponse]
    total: int
