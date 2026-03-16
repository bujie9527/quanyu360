"""Site plan request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class SitePlanItemInput(BaseModel):
    site_name: str = Field(min_length=1, max_length=255)
    site_theme: str = Field(min_length=1, max_length=255)
    target_audience: str = Field(min_length=1)
    content_direction: str = Field(min_length=1)
    seo_keywords: list[str] = Field(default_factory=list)
    site_structure: dict = Field(default_factory=dict)


class SitePlanCreateRequest(BaseModel):
    agent_input: dict = Field(default_factory=dict)
    agent_output: dict = Field(default_factory=dict)
    items: list[SitePlanItemInput] = Field(default_factory=list)


class SitePlanApproveRequest(BaseModel):
    approved_by: UUID | None = None


class SitePlanItemResponse(BaseModel):
    id: UUID
    site_name: str
    site_theme: str
    target_audience: str
    content_direction: str
    seo_keywords: list[str]
    site_structure: dict
    wordpress_site_id: UUID | None
    status: str
    created_at: datetime
    updated_at: datetime


class SitePlanResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    agent_input: dict
    agent_output: dict
    approved_at: datetime | None
    approved_by: UUID | None
    items: list[SitePlanItemResponse]
    created_at: datetime
    updated_at: datetime


class SitePlanListResponse(BaseModel):
    items: list[SitePlanResponse]
    total: int
