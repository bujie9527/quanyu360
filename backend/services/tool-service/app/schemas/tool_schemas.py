"""Tool request/response schemas (stub)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ToolSummaryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    tool_type: str
    created_at: datetime
    updated_at: datetime


class ToolListResponse(BaseModel):
    items: list[ToolSummaryResponse]
    total: int
