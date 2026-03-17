"""WordPress site request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class WordPressSiteCreateRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1, max_length=255)
    api_url: str = Field(min_length=1, max_length=512)
    username: str = Field(min_length=1, max_length=120)
    app_password: str = Field(min_length=1, max_length=255)


class WordPressSiteResponse(BaseModel):
    id: UUID
    tenant_id: UUID | None
    project_id: UUID | None
    server_id: UUID | None = None
    install_task_run_id: UUID | None = None
    name: str
    domain: str
    api_url: str
    username: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class WordPressSiteDetailResponse(WordPressSiteResponse):
    """Detail response - app_password is never returned."""


class WordPressSiteTestResponse(BaseModel):
    success: bool
    message: str
    site_name: str | None = None
    wp_version: str | None = None


class WordPressSiteCredentialsUpdateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    app_password: str = Field(min_length=1, max_length=255)
    status: str = Field(default="active", pattern="^(active|inactive|error)$")
