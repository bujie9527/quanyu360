"""HTTP/REST API tool - calls external APIs using connector_config (Tool.config)."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.connectors.base import ConnectorConfig
from tools.connectors.http_connector import HttpConnector
from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class HttpRequestParams(BaseModel):
    path: str = Field(description="API path, e.g. /users or POST /users")
    query: dict[str, str] | None = Field(default=None, description="Query parameters")
    body: dict | None = Field(default=None, description="Request body for POST/PUT")


class HttpApiTool(StructuredTool):
    """Call external REST APIs. Requires connector_config with base_url, api_key (optional)."""

    name = "http_api"
    description = "Call external REST APIs. Config: base_url, api_key, headers."

    action_models = {"request": HttpRequestParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "request": ToolActionDefinition(
                name="request",
                description="Execute HTTP request. path format: METHOD /path or /path (GET)",
                parameters=[
                    ToolParameterDefinition(name="path", type="string", description="e.g. GET /users or POST /orders"),
                    ToolParameterDefinition(name="query", type="object", required=False, description="Query params"),
                    ToolParameterDefinition(name="body", type="object", required=False, description="JSON body"),
                ],
            ),
        }

    def handle(self, action: str, payload: BaseModel, context: ToolExecutionContext) -> ToolExecutionResult:
        if action != "request":
            return ToolExecutionResult(tool_name=self.name, action=action, success=False, error_message="Unknown action")
        config = ConnectorConfig(context.connector_config)
        params = {"query": payload.query or {}, "body": payload.body}
        action_spec = payload.path
        result = HttpConnector().execute(action=action_spec, parameters=params, config=config)
        success = result.get("success", False)
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=success,
            output=result,
            error_message=None if success else result.get("error", str(result)),
        )
