"""Usage ingest request schema."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class UsageSummaryResponse(BaseModel):
    tenant_id: UUID
    llm_tokens_total: int
    llm_prompt_tokens: int
    llm_completion_tokens: int
    workflow_runs: int
    tool_executions: int
    from_at: datetime | None = None
    to_at: datetime | None = None


class UsageIngestRequest(BaseModel):
    tenant_id: str | UUID
    project_id: str | UUID | None = None
    usage_type: str = Field(..., pattern="^(llm_tokens|workflow_run|tool_execution)$")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    quantity: int = Field(default=1, ge=0)
    metadata: dict = Field(default_factory=dict)


class UsageLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    usage_type: str
    project_id: UUID | None
    prompt_tokens: int
    completion_tokens: int
    quantity: int
    created_at: datetime


class UsageListResponse(BaseModel):
    items: list[UsageLogResponse]
    total: int


class QuotaResourceResponse(BaseModel):
    current: int
    limit: int
    allowed: bool


class QuotaListResponse(BaseModel):
    tenant_id: UUID
    quotas: dict[str, QuotaResourceResponse]


class QuotaUpdateRequest(BaseModel):
    tasks_per_month: int | None = Field(default=None, ge=0)
    llm_requests_per_month: int | None = Field(default=None, ge=0)
    workflows_per_month: int | None = Field(default=None, ge=0)
    wordpress_sites_per_month: int | None = Field(default=None, ge=0)
