"""Project request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from common.app.models import ProjectStatus
from common.app.models import ProjectType
from common.app.models import UserRole


class ProjectTeamMemberInput(BaseModel):
    user_id: UUID
    role: UserRole = UserRole.operator


class ProjectCreateRequest(BaseModel):
    tenant_id: UUID
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    owner_id: UUID | None = None
    project_type: ProjectType = ProjectType.general
    matrix_config: dict = Field(default_factory=dict)
    team_members: list[ProjectTeamMemberInput] = Field(default_factory=list)
    agent_ids: list[UUID] = Field(default_factory=list)
    workflow_ids: list[UUID] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    owner_id: UUID | None = None
    status: ProjectStatus | None = None
    project_type: ProjectType | None = None
    matrix_config: dict | None = None
    team_members: list[ProjectTeamMemberInput] | None = None
    agent_ids: list[UUID] | None = None
    workflow_ids: list[UUID] | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class TeamMemberResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    role: UserRole


class ProjectAgentResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    model: str


class ProjectWorkflowResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    version: int


class ProjectTaskResponse(BaseModel):
    id: UUID
    title: str
    status: str
    priority: str
    agent_id: UUID | None
    workflow_id: UUID | None


class ProjectSummaryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    key: str
    name: str
    description: str | None
    owner_id: UUID | None
    status: str
    project_type: str
    matrix_config: dict
    team_members: list[TeamMemberResponse]
    agent_count: int
    task_count: int
    workflow_count: int
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    key: str
    name: str
    description: str | None
    owner_id: UUID | None
    status: str
    project_type: str
    matrix_config: dict
    team_members: list[TeamMemberResponse]
    agents: list[ProjectAgentResponse]
    tasks: list[ProjectTaskResponse]
    workflows: list[ProjectWorkflowResponse]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectSummaryResponse]
    total: int
