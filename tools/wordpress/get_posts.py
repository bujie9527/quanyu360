"""GetPostsTool: 获取 WordPress 文章列表。"""
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


class GetPostsInput(SiteInputMixin):
    per_page: int = Field(default=10, ge=1, le=100, description="每页数量")
    page: int = Field(default=1, ge=1, description="页码")
    status: str | None = Field(default=None, description="筛选状态: publish/draft/pending/private")
    search: str | None = Field(default=None, description="搜索关键词")


class GetPostsTool(StructuredTool):
    """获取 WordPress 文章列表。GET /wp/v2/posts"""

    name = "wordpress_get_posts"
    description = "获取 WordPress 站点文章列表。需 site_id，可选分页和筛选。"
    action_models = {"get_posts": GetPostsInput}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "get_posts": ToolActionDefinition(
                name="get_posts",
                description="获取文章列表",
                parameters=[
                    ToolParameterDefinition(name="site_id", type="string", description="WordPress 站点 ID"),
                    ToolParameterDefinition(name="per_page", type="integer", required=False, description="每页数量 (默认 10)"),
                    ToolParameterDefinition(name="page", type="integer", required=False, description="页码 (默认 1)"),
                    ToolParameterDefinition(name="status", type="string", required=False, description="状态筛选"),
                    ToolParameterDefinition(name="search", type="string", required=False, description="搜索关键词"),
                ],
            ),
        }

    def handle(self, action: str, payload: GetPostsInput, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            creds = resolve_site_credentials(payload.site_id, _get_tenant_id(context))
        except (ValueError, RuntimeError) as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        params = {"per_page": payload.per_page, "page": payload.page}
        if payload.status:
            params["status"] = payload.status
        if payload.search:
            params["search"] = payload.search

        success, data = _wp_request(creds, "GET", "/wp/v2/posts", params=params)

        if not success:
            return _tool_result(False, data, context, action, self.name)

        posts = data if isinstance(data, list) else (data.get("items", []) or [])
        items = []
        for p in posts:
            if isinstance(p, dict):
                items.append({
                    "id": p.get("id"),
                    "title": p.get("title", {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title", "")),
                    "status": p.get("status"),
                    "link": p.get("link"),
                    "date": p.get("date"),
                })
        output = {"posts": items, "total": len(items)}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
