"""GenerateMetaTool: 生成 meta_title 和 meta_description。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.seo.llm_client import llm_generate_json


class GenerateMetaParams(BaseModel):
    title: str = Field(default="", description="文章标题")
    content: str = Field(..., description="文章内容")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")


class GenerateMetaTool(StructuredTool):
    """SEO meta 标签生成，通过 LLM 生成 meta_title 和 meta_description。"""

    name = "seo_generate_meta"
    description = "根据标题、内容和关键词生成 SEO 优化的 meta_title 和 meta_description。"
    action_models = {"generate": GenerateMetaParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "generate": ToolActionDefinition(
                name="generate",
                description="生成 meta_title 和 meta_description",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="keywords", type="array", required=False, description="关键词列表"),
                ],
            ),
        }

    def handle(self, action: str, payload: GenerateMetaParams, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            result = llm_generate_json(
                "You are an SEO expert. Generate meta_title (max 60 chars) and meta_description (max 160 chars) "
                "for the given content. Output JSON: {\"meta_title\": \"...\", \"meta_description\": \"...\"}",
                f"Title: {payload.title}\n\nContent: {(payload.content or '')[:2000]}\n\nKeywords: {payload.keywords}",
            )
        except RuntimeError as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        meta_title = ""
        meta_description = ""
        if isinstance(result, dict):
            meta_title = str(result.get("meta_title", "")).strip() or payload.title[:60]
            meta_description = str(result.get("meta_description", "")).strip()

        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output={"meta_title": meta_title, "meta_description": meta_description},
        )
