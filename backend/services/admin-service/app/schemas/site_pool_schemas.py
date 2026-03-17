"""Schemas for admin site pool and batch install."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class SitePoolBatchInstallRequest(BaseModel):
    server_id: UUID
    domain_ids: list[UUID] = Field(min_length=1, max_length=200)
    workflow_id: UUID | None = None
    admin_username: str = Field(default="admin", min_length=1, max_length=120)
    admin_password: str = Field(min_length=6, max_length=255)
    admin_email: str = Field(min_length=3, max_length=255)
    site_title_prefix: str = Field(default="Matrix Site", min_length=1, max_length=120)


class SitePoolBatchInstallResponse(BaseModel):
    site_ids: list[UUID]
    task_run_ids: list[UUID]


class SitePoolAssignRequest(BaseModel):
    tenant_id: UUID
    project_id: UUID


class SitePoolStepLogResponse(BaseModel):
    id: UUID
    step_name: str
    status: str
    duration: float
    output_json: dict[str, object]
    created_at: datetime


class SitePoolInstallRunResponse(BaseModel):
    task_run_id: UUID
    status: str
    start_time: datetime
    end_time: datetime | None
    steps: list[SitePoolStepLogResponse]


class SitePoolSiteResponse(BaseModel):
    id: UUID
    domain: str
    name: str
    api_url: str
    status: str
    pool_status: str
    platform_domain_id: UUID | None
    server_id: UUID | None
    install_task_run_id: UUID | None
    tenant_id: UUID | None
    project_id: UUID | None
    created_at: datetime
    updated_at: datetime


class SitePoolSiteListResponse(BaseModel):
    items: list[SitePoolSiteResponse]
    total: int


class SitePoolInstallWorkflowResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    status: str


class SitePoolInstallWorkflowListResponse(BaseModel):
    items: list[SitePoolInstallWorkflowResponse]
    total: int
