"""UpdatePostTool: 更新 WordPress 文章。"""
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


class UpdatePostInput(SiteInputMixin):
    post_id: str = Field(..., description="WordPress 文章 ID")
    title: str | None = Field(default=None, description="新标题")
    content: str | None = Field(default=None, description="新内容")
    status: str | None = Field(default=None, description="新状态")


class UpdatePostTool(StructuredTool):
    """更新 WordPress 文章。POST /wp/v2/posts/{id}"""

    name = "wordpress_update_post"
    description = "更新已有 WordPress 文章。需 site_id、post_id，至少提供一个更新字段。"
    action_models = {"update": UpdatePostInput}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "update": ToolActionDefinition(
                name="update",
                description="更新文章",
                parameters=[
                    ToolParameterDefinition(name="site_id", type="string", description="WordPress 站点 ID"),
                    ToolParameterDefinition(name="post_id", type="string", description="文章 ID"),
                    ToolParameterDefinition(name="title", type="string", required=False, description="新标题"),
                    ToolParameterDefinition(name="content", type="string", required=False, description="新内容"),
                    ToolParameterDefinition(name="status", type="string", required=False, description="新状态"),
                ],
            ),
        }

    def handle(self, action: str, payload: UpdatePostInput, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            creds = resolve_site_credentials(payload.site_id, _get_tenant_id(context))
        except (ValueError, RuntimeError) as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        body = {}
        if payload.title is not None:
            body["title"] = {"raw": payload.title}
        if payload.content is not None:
            body["content"] = {"raw": payload.content}
        if payload.status is not None:
            body["status"] = payload.status

        if not body:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message="至少需要提供 title、content 或 status",
            )

        success, data = _wp_request(creds, "POST", f"/wp/v2/posts/{payload.post_id}", json=body)

        if not success:
            return _tool_result(False, data, context, action, self.name)

        post_id = data.get("id")
        link = data.get("link") or ""
        output = {"post_id": post_id, "url": link}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
