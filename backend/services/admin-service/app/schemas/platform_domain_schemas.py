"""Platform domain request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class PlatformDomainCreateRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=255)
    api_base_url: str = Field(min_length=1, max_length=512)
    server_id: UUID | None = None
    ssl_enabled: bool = True
    status: str = Field(default="available", pattern="^(available|assigned|inactive)$")


class PlatformDomainUpdateRequest(BaseModel):
    domain: str | None = Field(default=None, min_length=1, max_length=255)
    api_base_url: str | None = Field(default=None, min_length=1, max_length=512)
    server_id: UUID | None = None
    ssl_enabled: bool | None = None
    status: str | None = Field(default=None, pattern="^(available|assigned|inactive)$")


class PlatformDomainResponse(BaseModel):
    id: UUID
    domain: str
    api_base_url: str
    server_id: UUID | None
    ssl_enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime


class PlatformDomainListResponse(BaseModel):
    items: list[PlatformDomainResponse]
    total: int
