"""GenerateTagsTool: 生成 SEO 标签。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.seo.llm_client import llm_generate_json


class GenerateTagsParams(BaseModel):
    title: str = Field(default="", description="文章标题")
    content: str = Field(..., description="文章内容")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")


class GenerateTagsTool(StructuredTool):
    """SEO 标签生成，通过 LLM 生成内容相关标签。"""

    name = "seo_generate_tags"
    description = "根据标题、内容和关键词生成 SEO 优化的标签列表。"
    action_models = {"generate": GenerateTagsParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "generate": ToolActionDefinition(
                name="generate",
                description="生成标签列表",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="keywords", type="array", required=False, description="关键词列表"),
                ],
            ),
        }

    def handle(self, action: str, payload: GenerateTagsParams, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            result = llm_generate_json(
                "You are an SEO expert. Generate 5-15 relevant tags for the content. "
                "Output JSON: {\"tags\": [\"tag1\", \"tag2\", ...]}. Use concise, topic-relevant tags.",
                f"Title: {payload.title}\n\nContent: {(payload.content or '')[:2000]}\n\nKeywords: {payload.keywords}",
            )
        except RuntimeError as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        tags = []
        if isinstance(result, dict):
            tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]
        tags = [str(t).strip() for t in tags if t]

        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output={"tags": tags},
        )
