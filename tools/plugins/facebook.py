"""Facebook/Meta Graph API integration. create_post, comment_post, send_message with rate limiting."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.connectors.base import ConnectorConfig
from tools.connectors.facebook_connector import FacebookConnector
from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class CreatePostParams(BaseModel):
    page_id: str = Field(min_length=1, max_length=120)
    message: str = Field(default="", min_length=0)
    link: str | None = None


class CommentPostParams(BaseModel):
    post_id: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1)


class SendMessageParams(BaseModel):
    page_id: str = Field(min_length=1, max_length=120)
    recipient_id: str = Field(min_length=1, max_length=120, description="Messenger PSID")
    message: str = Field(min_length=1)
    messaging_type: str = Field(default="RESPONSE", description="RESPONSE, UPDATE, MESSAGE_TAG")


class FacebookTool(StructuredTool):
    """
    Facebook/Meta Graph API: page posts, comments, Messenger.
    Credentials: connector_config.access_token or FACEBOOK_ACCESS_TOKEN.
    Rate limiting: X-App-Usage aware, 429 retry with backoff.
    """

    name = "facebook"
    description = "Facebook Graph API: create posts, comment, send Messenger messages. Includes rate limiting."

    action_models = {
        "create_post": CreatePostParams,
        "comment_post": CommentPostParams,
        "send_message": SendMessageParams,
    }

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "create_post": ToolActionDefinition(
                name="create_post",
                description="Create a Facebook Page post. Either message or link required.",
                parameters=[
                    ToolParameterDefinition(name="page_id", type="string", description="Facebook Page ID"),
                    ToolParameterDefinition(name="message", type="string", required=False, description="Post text"),
                    ToolParameterDefinition(name="link", type="string", required=False, description="URL to attach"),
                ],
            ),
            "comment_post": ToolActionDefinition(
                name="comment_post",
                description="Comment on a Facebook post.",
                parameters=[
                    ToolParameterDefinition(name="post_id", type="string", description="Post ID (page_post_id)"),
                    ToolParameterDefinition(name="message", type="string", description="Comment text"),
                ],
            ),
            "send_message": ToolActionDefinition(
                name="send_message",
                description="Send a Messenger message. Recipient must have messaged Page within 24h or opted in.",
                parameters=[
                    ToolParameterDefinition(name="page_id", type="string", description="Facebook Page ID"),
                    ToolParameterDefinition(name="recipient_id", type="string", description="Recipient PSID (Page-Scoped ID)"),
                    ToolParameterDefinition(name="message", type="string", description="Message text"),
                    ToolParameterDefinition(name="messaging_type", type="string", required=False, description="RESPONSE, UPDATE, or MESSAGE_TAG"),
                ],
            ),
        }

    def handle(self, action: str, payload: BaseModel, context: ToolExecutionContext) -> ToolExecutionResult:
        config = ConnectorConfig(context.connector_config)
        connector = FacebookConnector()

        if action == "create_post":
            params = {
                "page_id": payload.page_id,
                "message": payload.message or "",
                "link": payload.link,
            }
        elif action == "comment_post":
            params = {"post_id": payload.post_id, "message": payload.message}
        elif action == "send_message":
            params = {
                "page_id": payload.page_id,
                "recipient_id": payload.recipient_id,
                "message": payload.message,
                "messaging_type": payload.messaging_type,
            }
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
