"""WordPress REST API integration. publish_post, update_post, delete_post. Credentials via connector_config."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.connectors.base import ConnectorConfig
from tools.connectors.wordpress_connector import WordPressConnector
from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class PublishPostParams(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    status: str = Field(default="draft", pattern="^(draft|publish|pending|private|future)$")
    author: str | None = None
    tags: list[str] = Field(default_factory=list)


class UpdatePostParams(BaseModel):
    post_id: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class DeletePostParams(BaseModel):
    post_id: str = Field(min_length=1, max_length=120)
    force: bool = Field(default=True, description="Bypass Trash and force permanent deletion")


class WordPressTool(StructuredTool):
    """
    WordPress content publishing via REST API.
    Credentials: connector_config.basic_auth {user, password} + base_url,
    or env WORDPRESS_SITE_URL, WORDPRESS_USER, WORDPRESS_APP_PASSWORD.
    """

    name = "wordpress"
    description = "WordPress REST API: publish, update, and delete posts."

    action_models = {
        "publish_post": PublishPostParams,
        "update_post": UpdatePostParams,
        "delete_post": DeletePostParams,
    }

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "publish_post": ToolActionDefinition(
                name="publish_post",
                description="Create and publish a new WordPress post via REST API.",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", description="Post title"),
                    ToolParameterDefinition(name="content", type="string", description="Post body (HTML supported)"),
                    ToolParameterDefinition(name="status", type="string", required=False, description="draft, publish, pending, private, or future"),
                    ToolParameterDefinition(name="author", type="string", required=False, description="WordPress author ID"),
                    ToolParameterDefinition(name="tags", type="array", required=False, description="Tag IDs"),
                ],
            ),
            "update_post": ToolActionDefinition(
                name="update_post",
                description="Update an existing WordPress post.",
                parameters=[
                    ToolParameterDefinition(name="post_id", type="string", description="WordPress post ID"),
                    ToolParameterDefinition(name="title", type="string", required=False, description="Updated title"),
                    ToolParameterDefinition(name="content", type="string", required=False, description="Updated content"),
                    ToolParameterDefinition(name="status", type="string", required=False, description="Updated status"),
                    ToolParameterDefinition(name="tags", type="array", required=False, description="Updated tag IDs"),
                ],
            ),
            "delete_post": ToolActionDefinition(
                name="delete_post",
                description="Delete a WordPress post. Use force=true to bypass Trash.",
                parameters=[
                    ToolParameterDefinition(name="post_id", type="string", description="WordPress post ID"),
                    ToolParameterDefinition(name="force", type="boolean", required=False, description="Force permanent deletion (default true)"),
                ],
            ),
        }

    def handle(self, action: str, payload: BaseModel, context: ToolExecutionContext) -> ToolExecutionResult:
        config = ConnectorConfig(context.connector_config)
        connector = WordPressConnector()

        if action == "publish_post":
            params = {
                "title": payload.title,
                "content": payload.content,
                "status": payload.status,
                "author": payload.author,
                "tags": payload.tags,
            }
        elif action == "update_post":
            params = {
                "post_id": payload.post_id,
                "title": payload.title,
                "content": payload.content,
                "status": payload.status,
                "tags": payload.tags,
            }
        elif action == "delete_post":
            params = {"post_id": payload.post_id, "force": payload.force}
        else:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=f"Unknown action: {action}",
            )

        result = connector.execute(action=action, parameters=params, config=config)
        success = result.get("success", False)
        output = {
            "status_code": result.get("status_code"),
            "data": result.get("data"),
            "agent_id": context.agent_id,
        }
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=success,
            output=output,
            error_message=None if success else result.get("error", str(result)),
        )
