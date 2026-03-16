"""Tool HTTP endpoints."""
from fastapi import APIRouter
from fastapi import Depends

from app.dependencies import get_tool_service
from app.schemas.tool_schemas import ToolListResponse
from app.services import ToolService

router = APIRouter()


@router.get("/tools", response_model=ToolListResponse, tags=["tools"])
def list_tools(tool_service: ToolService = Depends(get_tool_service)) -> ToolListResponse:
    return tool_service.list_tools()

