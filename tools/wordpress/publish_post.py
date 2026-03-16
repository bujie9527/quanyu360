"""PublishPostTool: 发布 WordPress 文章。"""
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


class PublishPostInput(SiteInputMixin):
    title: str = Field(..., min_length=1, description="文章标题")
    content: str = Field(..., description="文章内容 (支持 HTML)")
    status: str = Field(default="publish", description="publish | draft | pending | private | future")


class PublishPostTool(StructuredTool):
    """发布 WordPress 文章。POST /wp/v2/posts"""

    name = "wordpress_publish_post"
    description = "发布文章到 WordPress 站点。需 site_id、title、content，可选 status。"
    action_models = {"publish": PublishPostInput}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "publish": ToolActionDefinition(
                name="publish",
                description="发布新文章",
                parameters=[
                    ToolParameterDefinition(name="site_id", type="string", description="WordPress 站点 ID"),
                    ToolParameterDefinition(name="title", type="string", description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="status", type="string", required=False, description="publish/draft/pending/private/future"),
                ],
            ),
        }

    def handle(self, action: str, payload: PublishPostInput, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            creds = resolve_site_credentials(payload.site_id, _get_tenant_id(context))
        except (ValueError, RuntimeError) as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        body = {
            "title": {"raw": payload.title},
            "content": {"raw": payload.content},
            "status": payload.status or "publish",
        }
        success, data = _wp_request(creds, "POST", "/wp/v2/posts", json=body)

        if not success:
            return _tool_result(False, data, context, action, self.name)

        post_id = data.get("id")
        link = data.get("link") or (data.get("guid", {}) or {}).get("rendered", "") if isinstance(data.get("guid"), dict) else ""
        output = {"post_id": post_id, "url": link or f"{creds.api_url.rstrip('/')}/?p={post_id}"}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
