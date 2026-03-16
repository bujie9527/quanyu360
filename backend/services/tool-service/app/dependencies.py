"""Dependency injection."""
from app.services import ToolService


def get_tool_service() -> ToolService:
    return ToolService()
