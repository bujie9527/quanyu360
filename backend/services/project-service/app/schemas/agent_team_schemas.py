"""Agent team request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from common.app.models import TeamExecutionType


class AgentTeamMemberInput(BaseModel):
    """Input for adding an agent to a team."""
    agent_id: UUID
    role_in_team: str = Field(min_length=1, max_length=120)
    order_index: int = 0


class AgentTeamCreateRequest(BaseModel):
    """Request to create an agent team."""
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    execution_type: TeamExecutionType = TeamExecutionType.sequential
    members: list[AgentTeamMemberInput] = Field(default_factory=list)


class AgentTeamUpdateRequest(BaseModel):
    """Request to update an agent team."""
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    execution_type: TeamExecutionType | None = None
    members: list[AgentTeamMemberInput] | None = None


class AgentTeamMemberResponse(BaseModel):
    """Response for a team member."""
    id: UUID
    agent_id: UUID
    agent_name: str
    role_in_team: str
    order_index: int


class AgentTeamSummaryResponse(BaseModel):
    """Summary of an agent team."""
    id: UUID
    project_id: UUID
    name: str
    slug: str
    description: str | None
    execution_type: str
    member_count: int
    created_at: datetime
    updated_at: datetime


class AgentTeamDetailResponse(BaseModel):
    """Full detail of an agent team with members."""
    id: UUID
    project_id: UUID
    name: str
    slug: str
    description: str | None
    execution_type: str
    members: list[AgentTeamMemberResponse]
    created_at: datetime
    updated_at: datetime


class AgentTeamListResponse(BaseModel):
    """List of agent teams."""
    items: list[AgentTeamSummaryResponse]
    total: int
