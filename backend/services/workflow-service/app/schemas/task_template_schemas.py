"""TaskTemplate request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class TaskTemplateCreateRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    workflow_id: UUID | None = Field(default=None)
    parameters_schema: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class TaskTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    workflow_id: UUID | None = None
    parameters_schema: dict[str, Any] | None = None
    enabled: bool | None = None


class TaskTemplateResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    workflow_id: UUID | None
    parameters_schema: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskTemplateListResponse(BaseModel):
    items: list[TaskTemplateResponse]
    total: int
