"""FetchContentTool: 从工作流输入或 Content Source 获取内容。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class FetchContentParams(BaseModel):
    """获取内容参数。可来自工作流输入或 prior 步骤输出。"""

    content: str = Field(default="", description="文章内容")
    title: str = Field(default="", description="文章标题")


class FetchContentTool(StructuredTool):
    """
    获取内容步骤。用于工作流中从输入 payload 或上游步骤获取 content/title。
    若参数为空，会尝试从 prior_workflow_output 中读取。
    """

    name = "fetch_content"
    description = "从工作流输入或上游步骤获取文章内容和标题，供后续 SEO 与发布使用。"
    action_models = {"fetch": FetchContentParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "fetch": ToolActionDefinition(
                name="fetch",
                description="获取内容与标题",
                parameters=[
                    ToolParameterDefinition(name="content", type="string", required=False, description="文章内容"),
                    ToolParameterDefinition(name="title", type="string", required=False, description="文章标题"),
                ],
            ),
        }

    def handle(self, action: str, payload: FetchContentParams, context: ToolExecutionContext) -> ToolExecutionResult:
        content = (payload.content or "").strip()
        title = (payload.title or "").strip()
        metadata: dict[str, Any] = context.metadata or {}
        prior = metadata.get("prior_output") or metadata.get("prior_workflow_output") or metadata.get("_last_output")
        if isinstance(prior, dict):
            content = content or str(prior.get("content", "") or "")
            title = title or str(prior.get("title", prior.get("content", ""))[:200] or "")

        output = {"content": content, "title": title or content[:60] if content else ""}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
