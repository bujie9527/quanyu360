"""SEO analysis and optimization tool. Discovered at runtime from tools/seo/tool.py."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class AnalyzeKeywordsParams(BaseModel):
    content: str = Field(min_length=1, description="Text to analyze for keywords")
    limit: int = Field(default=10, ge=1, le=50, description="Max keywords to return")


class SEOTool(StructuredTool):
    """
    SEO analysis and optimization. Keyword extraction, readability scoring.
    """

    name = "seo"
    description = "SEO analysis: extract keywords, analyze content for search optimization."

    action_models = {
        "analyze_keywords": AnalyzeKeywordsParams,
    }

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "analyze_keywords": ToolActionDefinition(
                name="analyze_keywords",
                description="Extract likely keywords from content for SEO.",
                parameters=[
                    ToolParameterDefinition(name="content", type="string", description="Text to analyze"),
                    ToolParameterDefinition(name="limit", type="integer", required=False, description="Max keywords (default 10)"),
                ],
            ),
        }

    def handle(self, action: str, payload: BaseModel, context: ToolExecutionContext) -> ToolExecutionResult:
        if action == "analyze_keywords":
            words = [
                w.strip().lower()
                for w in payload.content.split()
                if len(w.strip()) > 2
            ]
            from collections import Counter
            top = Counter(words).most_common(payload.limit)
            keywords = [{"keyword": k, "count": c} for k, c in top]
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=True,
                output={"keywords": keywords, "total_analyzed": len(words)},
            )
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=False,
            error_message=f"Unknown action: {action}",
        )


__all__ = ["SEOTool"]
