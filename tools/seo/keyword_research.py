"""KeywordResearchTool: 关键词研究与提取。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.seo.llm_client import llm_generate_json


class KeywordResearchParams(BaseModel):
    title: str = Field(default="", description="文章标题")
    content: str = Field(..., description="文章内容")
    keywords: list[str] = Field(default_factory=list, description="已有关键词")


class KeywordResearchTool(StructuredTool):
    """SEO 关键词研究与提取，通过 LLM 分析内容生成关键词。"""

    name = "seo_keyword_research"
    description = "基于标题和内容进行关键词研究，提取或扩展 SEO 关键词。"
    action_models = {"research": KeywordResearchParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "research": ToolActionDefinition(
                name="research",
                description="分析内容并生成 SEO 关键词列表",
                parameters=[
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                    ToolParameterDefinition(name="content", type="string", description="文章内容"),
                    ToolParameterDefinition(name="keywords", type="array", required=False, description="已有关键词"),
                ],
            ),
        }

    def handle(self, action: str, payload: KeywordResearchParams, context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            result = llm_generate_json(
                "You are an SEO expert. Analyze the content and output a JSON object with a single key 'keywords' "
                "containing a list of relevant SEO keywords (10-20 items). "
                "Prioritize semantic relevance and search intent.",
                f"Title: {payload.title}\n\nContent: {(payload.content or '')[:3000]}\n\n"
                f"Existing keywords (optional): {payload.keywords}",
            )
        except RuntimeError as e:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(e),
            )

        keywords = result.get("keywords", []) if isinstance(result, dict) else []
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
        keywords = [str(k).strip() for k in keywords if k]

        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output={"keywords": keywords},
        )
