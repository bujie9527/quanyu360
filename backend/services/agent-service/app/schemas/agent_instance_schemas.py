"""AgentInstance request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class AgentInstanceCreateRequest(BaseModel):
    """创建 Agent Instance：从 AgentTemplate 复制配置。"""
    template_id: UUID = Field(description="AgentTemplate ID")
    name: str = Field(min_length=1, max_length=255)
    project_id: UUID
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if v else v


class AgentInstanceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = None
    model: str | None = Field(default=None, max_length=120)
    tools_override: list[str] | None = None
    knowledge_base_id: UUID | None = None
    config: dict[str, object] | None = None
    enabled: bool | None = None


class AgentInstanceDetailResponse(BaseModel):
    """Agent Instance 详情/列表项。default_tools 为有效工具列表（template 复制 + tools_override 覆盖）。"""
    id: UUID
    tenant_id: UUID
    project_id: UUID
    template_id: UUID | None
    name: str
    description: str | None
    system_prompt: str
    model: str
    default_tools: list[str]
    default_workflows: list[str]
    tools_override: list[str]
    knowledge_base_id: UUID | None
    config: dict[str, object]
    enabled: bool
    created_at: str | None = None  # ISO format string for JSON
    template_name: str | None = None
    project_name: str | None = None
    knowledge_base_name: str | None = None


class AgentInstanceListResponse(BaseModel):
    items: list[AgentInstanceDetailResponse]
    total: int
