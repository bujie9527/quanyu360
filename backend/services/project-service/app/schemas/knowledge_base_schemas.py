"""Knowledge base request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    embedding_model: str = Field(default="text-embedding-3-small", max_length=80)


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    description: str | None
    embedding_model: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    filename: str
    mime_type: str | None
    status: str
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    content: str = Field(..., min_length=1)
    filename: str = Field(default="document.txt", max_length=255)
    mime_type: str | None = Field(default="text/plain")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: str
    score: float
    content: str
    document_id: str | None
    chunk_index: int | None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
