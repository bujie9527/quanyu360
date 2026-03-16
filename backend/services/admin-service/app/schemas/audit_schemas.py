"""Audit log API schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class AuditIngestRequest(BaseModel):
    """Request to ingest an audit log entry (from agent-runtime, workflow-engine, etc.)."""

    tenant_id: UUID
    project_id: UUID | None = None
    action: str = Field(description="create|update|delete|execute|assign|login")
    entity_type: str = Field(description="agent_run|tool_call|workflow_execution|task|project|...")
    entity_id: UUID | None = None
    correlation_id: str | None = None
    payload: dict = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """Audit log entry for list response."""

    id: str
    tenant_id: str
    project_id: str | None
    actor_user_id: str | None
    action: str
    entity_type: str
    entity_id: str | None
    correlation_id: str | None
    created_at: datetime
    payload: dict

    class Config:
        from_attributes = True
