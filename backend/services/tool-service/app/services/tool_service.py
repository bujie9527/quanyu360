"""Tool business logic (stub)."""
from app.schemas.tool_schemas import ToolListResponse


class ToolService:
    """Orchestrates tool business logic. Stub implementation."""

    def list_tools(self) -> ToolListResponse:
        return ToolListResponse(items=[], total=0)
