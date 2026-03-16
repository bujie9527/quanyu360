"""AgentTemplate request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class AgentTemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str = Field(default="")
    model: str = Field(default="gpt-4", max_length=120)
    default_tools: list[str] = Field(default_factory=list)
    default_workflows: list[str] = Field(default_factory=list)
    config_schema: dict[str, object] = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if v else v


class AgentTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, v: str | None) -> str | None:
        return v.strip() if v and isinstance(v, str) else v

    system_prompt: str | None = None
    model: str | None = Field(default=None, max_length=120)
    default_tools: list[str] | None = None
    default_workflows: list[str] | None = None
    config_schema: dict[str, object] | None = None
    enabled: bool | None = None


class AgentTemplateDetailResponse(BaseModel):
    """返回结构：id, name, description, model, default_tools, default_workflows, system_prompt, enabled"""
    id: UUID
    name: str
    description: str | None
    model: str
    default_tools: list[str]
    default_workflows: list[str]
    system_prompt: str = ""
    enabled: bool = True


class AgentTemplateListResponse(BaseModel):
    items: list[AgentTemplateDetailResponse]
    total: int
