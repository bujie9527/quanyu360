"""Site building batch request/response schemas."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class SiteBuildingBatchRequest(BaseModel):
    project_id: UUID = Field(..., description="Project to create sites under")
    count: int = Field(..., ge=1, le=50, description="Number of sites to create")
    domain_ids: list[UUID] = Field(..., min_length=1, description="Platform domain IDs to use (must be available)")
    workflow_id: UUID | None = Field(default=None, description="Optional workflow for TaskRun creation (for frontend polling)")


class SiteBuildingBatchResponse(BaseModel):
    wordpress_site_ids: list[UUID]
    task_run_ids: list[UUID]
