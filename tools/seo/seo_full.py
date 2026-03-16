"""SEOFullTool: 一键生成完整 SEO 输出（meta_title, meta_description, tags, internal_links）。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.seo.llm_client import llm_generate_json


class SEOFullParams(BaseModel):
    title: str = Field(default="", description="文章标题")
    content: str = Field(..., description="文章内容")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")


class SEOFullTool(StructuredTool):
    """SEO 全量生成：一次调用 LLM 产出 meta_title、meta_description、tags、internal_links。"""

    name = "seo_full"
    description = "根据标题、内容和关键词一次性生成完整 SEO 输出：meta_title、meta_description、tags、internal_links。"
    action_models = {"generate": SEOFullParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "generate": ToolActionDefinition(
                name="generate",
                description="生成完整 SEO 输出",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="keywords", type="array", required=False, description="关键词列表"),
                ],
            ),
        }

    def handle(self, action: str, payload: SEOFullParams, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            result = llm_generate_json(
                "You are an SEO expert. Generate full SEO output for the content. "
                "Output JSON: {\"meta_title\": \"max 60 chars\", \"meta_description\": \"max 160 chars\", "
                "\"tags\": [\"tag1\", ...], \"internal_links\": [{\"anchor_text\": \"...\", \"target_url\": \"/path\", \"reason\": \"...\"}, ...]}. "
                "Provide 5-15 tags and 3-8 internal link suggestions.",
                f"Title: {payload.title}\n\nContent: {(payload.content or '')[:4000]}\n\nKeywords: {payload.keywords}",
            )
        except RuntimeError as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        if not isinstance(result, dict):
            result = {}

        meta_title = str(result.get("meta_title", "")).strip() or (payload.title[:60] if payload.title else "")
        meta_description = str(result.get("meta_description", "")).strip()
        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)] if tags else []
        tags = [str(t).strip() for t in tags if t]

        raw_links = result.get("internal_links", [])
        internal_links = []
        if isinstance(raw_links, list):
            for item in raw_links:
                if isinstance(item, dict):
                    internal_links.append({
                        "anchor_text": str(item.get("anchor_text", "")).strip(),
                        "target_url": str(item.get("target_url", "")).strip(),
                        "reason": str(item.get("reason", "")).strip(),
                    })
                elif isinstance(item, str):
                    internal_links.append({"anchor_text": item, "target_url": "", "reason": ""})

        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output={
                "meta_title": meta_title,
                "meta_description": meta_description,
                "tags": tags,
                "internal_links": internal_links,
            },
        )
