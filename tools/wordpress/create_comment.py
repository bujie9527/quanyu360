"""CreateCommentTool: 创建 WordPress 评论。"""
from __future__ import annotations

from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.wordpress.base import SiteInputMixin
from tools.wordpress.base import _get_tenant_id
from tools.wordpress.base import _tool_result
from tools.wordpress.base import _wp_request
from tools.wordpress.site_resolver import resolve_site_credentials


class CreateCommentInput(SiteInputMixin):
    post_id: str = Field(..., description="文章 ID")
    content: str = Field(..., min_length=1, description="评论内容")
    parent_id: int | None = Field(default=None, description="父评论 ID（回复用）")


class CreateCommentTool(StructuredTool):
    """创建 WordPress 评论。POST /wp/v2/comments"""

    name = "wordpress_create_comment"
    description = "在 WordPress 文章下创建评论。需 site_id、post_id、content。"
    action_models = {"create": CreateCommentInput}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "create": ToolActionDefinition(
                name="create",
                description="创建评论",
                parameters=[
                    ToolParameterDefinition(name="site_id", type="string", description="WordPress 站点 ID"),
                    ToolParameterDefinition(name="post_id", type="string", description="文章 ID"),
                    ToolParameterDefinition(name="content", type="string", description="评论内容"),
                    ToolParameterDefinition(name="parent_id", type="integer", required=False, description="父评论 ID"),
                ],
            ),
        }

    def handle(self, action: str, payload: CreateCommentInput, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            creds = resolve_site_credentials(payload.site_id, _get_tenant_id(context))
        except (ValueError, RuntimeError) as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        body = {"post": int(payload.post_id), "content": payload.content}
        if payload.parent_id is not None:
            body["parent"] = payload.parent_id

        success, data = _wp_request(creds, "POST", "/wp/v2/comments", json=body)

        if not success:
            return _tool_result(False, data, context, action, self.name)

        comment_id = data.get("id")
        link = data.get("link") or ""
        output = {"comment_id": comment_id, "url": link}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
