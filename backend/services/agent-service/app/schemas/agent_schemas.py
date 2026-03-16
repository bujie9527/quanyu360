"""Agent request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from common.app.models import AgentStatus


class AgentSkillInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    proficiency_level: int = Field(default=3, ge=1, le=5)
    description: str | None = Field(default=None, max_length=2000)
    is_core: bool = True


class AgentToolAssignmentInput(BaseModel):
    tool_id: UUID
    is_enabled: bool = True
    invocation_timeout_seconds: int = Field(default=30, ge=1, le=3600)


class AgentCreateRequest(BaseModel):
    project_id: UUID
    created_by_user_id: UUID | None = None
    name: str = Field(min_length=2, max_length=255)
    role: str = Field(min_length=2, max_length=120)
    model: str = Field(min_length=2, max_length=120)
    system_prompt: str = Field(min_length=10, max_length=12000)
    role_title: str | None = Field(default=None, max_length=120)
    max_concurrency: int = Field(default=1, ge=1, le=100)
    status: AgentStatus = AgentStatus.draft
    skills: list[AgentSkillInput] = Field(default_factory=list)
    tools: list[AgentToolAssignmentInput] = Field(default_factory=list)
    workflow_ids: list[UUID] = Field(default_factory=list)
    config: dict[str, object] = Field(default_factory=dict)

    @field_validator("name", "role", "model", "system_prompt")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class AgentUpdateRequest(BaseModel):
    project_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    role: str | None = Field(default=None, min_length=2, max_length=120)
    role_title: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, min_length=2, max_length=120)
    system_prompt: str | None = Field(default=None, min_length=10, max_length=12000)
    max_concurrency: int | None = Field(default=None, ge=1, le=100)
    status: AgentStatus | None = None
    skills: list[AgentSkillInput] | None = None
    tools: list[AgentToolAssignmentInput] | None = None
    workflow_ids: list[UUID] | None = None
    config: dict[str, object] | None = None

    @field_validator("name", "role", "model", "system_prompt")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class AgentSkillResponse(BaseModel):
    id: UUID
    name: str
    category: str
    proficiency_level: int
    description: str | None
    is_core: bool


class AgentToolResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    tool_type: str
    is_enabled: bool
    invocation_timeout_seconds: int


class AgentWorkflowResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    version: int


class AgentToolPermissionResponse(BaseModel):
    id: UUID
    tool_slug: str


class AgentToolPermissionCreate(BaseModel):
    tool_slug: str = Field(min_length=1, max_length=120)


class AgentAllowedToolsResponse(BaseModel):
    agent_id: UUID
    allowed_tool_slugs: list[str]
    unrestricted: bool = False


class AgentSummaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    role: str
    role_title: str
    model: str
    status: str
    skill_count: int
    tool_count: int
    workflow_count: int
    created_at: datetime
    updated_at: datetime


class AgentDetailResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by_user_id: UUID | None
    name: str
    slug: str
    role: str
    role_title: str
    model: str
    system_prompt: str
    status: str
    max_concurrency: int
    config: dict[str, object]
    skills: list[AgentSkillResponse]
    tools: list[AgentToolResponse]
    tool_permissions: list[AgentToolPermissionResponse] = Field(default_factory=list)
    workflows: list[AgentWorkflowResponse]
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentSummaryResponse]
    total: int
