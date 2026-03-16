"""InternalLinkTool: 内部链接建议。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.seo.llm_client import llm_generate_json


class InternalLinkParams(BaseModel):
    title: str = Field(default="", description="文章标题")
    content: str = Field(..., description="文章内容")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")


class InternalLinkTool(StructuredTool):
    """SEO 内部链接建议，通过 LLM 生成锚文本与目标页面建议。"""

    name = "seo_internal_link"
    description = "根据内容生成内部链接建议，包含锚文本和目标 URL/页面主题。"
    action_models = {"suggest": InternalLinkParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "suggest": ToolActionDefinition(
                name="suggest",
                description="生成内部链接建议",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="keywords", type="array", required=False, description="关键词列表"),
                ],
            ),
        }

    def handle(self, action: str, payload: InternalLinkParams, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            result = llm_generate_json(
                "You are an SEO expert. Suggest 3-8 internal links for the content. "
                "Output JSON: {\"internal_links\": [{\"anchor_text\": \"...\", \"target_url\": \"/slug-or-path\", \"reason\": \"brief\"}, ...]}. "
                "target_url can be path-like (e.g. /blog/topic) or slug.",
                f"Title: {payload.title}\n\nContent: {(payload.content or '')[:3000]}\n\nKeywords: {payload.keywords}",
            )
        except RuntimeError as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        links = []
        if isinstance(result, dict):
            raw = result.get("internal_links", [])
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        links.append({
                            "anchor_text": str(item.get("anchor_text", "")).strip(),
                            "target_url": str(item.get("target_url", "")).strip(),
                            "reason": str(item.get("reason", "")).strip(),
                        })
                    elif isinstance(item, str):
                        links.append({"anchor_text": item, "target_url": "", "reason": ""})
            elif isinstance(raw, str):
                links.append({"anchor_text": raw, "target_url": "", "reason": ""})

        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output={"internal_links": links},
        )
