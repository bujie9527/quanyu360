"""System config request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class SystemConfigItemResponse(BaseModel):
    key: str
    value: str
    value_set: bool
    category: str
    is_secret: bool
    description: str | None
    updated_at: str | None


class SystemConfigUpdateRequest(BaseModel):
    value: str = Field(..., min_length=0)
    category: str | None = Field(default=None, max_length=60)
    is_secret: bool | None = None
    description: str | None = Field(default=None, max_length=500)


class SystemConfigBulkUpdateItem(BaseModel):
    key: str = Field(..., max_length=120)
    value: str = Field(..., min_length=0)
    category: str = Field(default="general", max_length=60)
    is_secret: bool = False
    description: str | None = Field(default=None, max_length=500)


class SystemConfigBulkUpdateRequest(BaseModel):
    items: list[SystemConfigBulkUpdateItem] = Field(..., min_length=1, max_length=100)
