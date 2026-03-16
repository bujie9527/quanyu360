"""LogResultTool: 记录工作流执行结果。"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition


class LogResultParams(BaseModel):
    """记录结果参数。"""

    message: str = Field(default="", description="附加日志信息")


class LogResultTool(StructuredTool):
    """
    记录工作流执行结果。用于流程末尾记录发布状态、URL 等信息。
    上游步骤输出会传入 parameters，一并记录。
    """

    name = "log_result"
    description = "记录工作流执行结果，用于审计与追踪。"
    action_models = {"log": LogResultParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "log": ToolActionDefinition(
                name="log",
                description="记录执行结果",
                parameters=[
                    ToolParameterDefinition(name="message", type="string", required=False, description="附加日志信息"),
                ],
            ),
        }

    def handle(self, action: str, payload: LogResultParams, context: ToolExecutionContext) -> ToolExecutionResult:
        message = (payload.message or "").strip()
        metadata: dict = context.metadata or {}
        prior = metadata.get("prior_output") or metadata.get("prior_workflow_output") or metadata.get("_last_output")
        result_summary: dict = {}
        if isinstance(prior, dict):
            result_summary = {k: v for k, v in prior.items() if k not in ("content",)}
        output = {"message": message or "Workflow completed", "result": result_summary}
        return ToolExecutionResult(
            tool_name=self.name,
            action=action,
            success=True,
            output=output,
        )
