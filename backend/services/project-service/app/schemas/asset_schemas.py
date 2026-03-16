"""Asset response schemas."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class AssetUploadResponse(BaseModel):
    id: UUID
    name: str
    storage_key: str
    kind: str
    mime_type: str | None
    size_bytes: int
