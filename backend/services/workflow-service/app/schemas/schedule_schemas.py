"""Schedule request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class ScheduleCreateRequest(BaseModel):
    task_template_id: UUID
    cron: str = Field(min_length=1, max_length=60)
    target_sites: list[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)


class ScheduleUpdateRequest(BaseModel):
    cron: str | None = Field(default=None, min_length=1, max_length=60)
    target_sites: list[str] | None = None
    enabled: bool | None = None


class ScheduleResponse(BaseModel):
    id: UUID
    task_template_id: UUID
    cron: str
    target_sites: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int


# Cron presets for hourly / daily / weekly
CRON_PRESETS = {
    "hourly": "0 * * * *",
    "daily": "0 9 * * *",
    "weekly": "0 9 * * 1",
}
