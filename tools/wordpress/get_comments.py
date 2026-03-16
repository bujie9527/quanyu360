"""GetCommentsTool: 获取 WordPress 评论列表。"""
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


class GetCommentsInput(SiteInputMixin):
    post_id: str = Field(..., description="文章 ID")
    per_page: int = Field(default=10, ge=1, le=100, description="每页数量")
    page: int = Field(default=1, ge=1, description="页码")


class GetCommentsTool(StructuredTool):
    """获取 WordPress 文章评论列表。GET /wp/v2/comments"""

    name = "wordpress_get_comments"
    description = "获取 WordPress 文章下的评论列表。需 site_id、post_id。"
    action_models = {"get_comments": GetCommentsInput}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "get_comments": ToolActionDefinition(
                name="get_comments",
                description="获取评论列表",
                parameters=[
                    ToolParameterDefinition(name="site_id", type="string", description="WordPress 站点 ID"),
                    ToolParameterDefinition(name="post_id", type="string", description="文章 ID"),
                    ToolParameterDefinition(name="per_page", type="integer", required=False, description="每页数量"),
                    ToolParameterDefinition(name="page", type="integer", required=False, description="页码"),
                ],
            ),
        }

    def handle(self, action: str, payload: GetCommentsInput, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            creds = resolve_site_credentials(payload.site_id, _get_tenant_id(context))
        except (ValueError, RuntimeError) as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        params = {"post": payload.post_id, "per_page": payload.per_page, "page": payload.page}
        success, data = _wp_request(creds, "GET", "/wp/v2/comments", params=params)

        if not success:
            return _tool_result(False, data, context, action, self.name)

        comments = data if isinstance(data, list) else (data.get("items", []) or [])
        items = []
        for c in comments:
            if isinstance(c, dict):
                items.append({
                    "id": c.get("id"),
                    "content": (c.get("content", {}) or {}).get("rendered", "") if isinstance(c.get("content"), dict) else str(c.get("content", "")),
                    "author_name": c.get("author_name"),
                    "date": c.get("date"),
                    "parent": c.get("parent"),
                })
        output = {"comments": items, "total": len(items)}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
