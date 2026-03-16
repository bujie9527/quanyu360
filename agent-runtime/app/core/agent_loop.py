"""AgentLoop: one iteration of plan → select tool → execute → observe → reflect → update memory."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone

import structlog

from app.core.config import get_settings
from app.core.execution_context import ExecutionContext
from app.core.reflection_service import ReflectionService
from app.core.schemas import ExecutionLogEntry
from app.core.tool_executor import ToolExecutor
from app.core.tool_selector import ToolSelector
from app.core.tooling import list_registered_tools


class AgentLoop:
    """
    Single iteration of the agent execution loop.
    Plan → Select tool → Execute → Observe → Reflect → Update memory.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="agent-loop")
        self.tool_selector = ToolSelector()
        self.tool_executor = ToolExecutor()
        self.reflection_service = ReflectionService()

    def step(self, ctx: ExecutionContext) -> bool:
        """
        Run one loop iteration. Returns True if more steps possible, False if done/error.
        """
        if ctx.is_exhausted():
            return False

        try:
            # Select tool (task augmented with observations)
            task_for_select = ctx.task_for_tool_selection()
            tool_call = self.tool_selector.select(
                task=task_for_select,
                available_tools=list_registered_tools(),
                model=ctx.request.model,
            )

            if tool_call is None:
                # No tool selected; reflect on current state and possibly finish
                result_to_reflect = ctx.accumulated_result or {"status": "no_tool_selected"}
                ctx.last_reflection = self.reflection_service.reflect(
                    task=ctx.request.task,
                    result=result_to_reflect,
                    status=ctx.status,
                    tool_results=ctx.tool_results,
                    model=ctx.request.model,
                )
                ctx.memory.add(
                    role="reflection",
                    content=f"Success={ctx.last_reflection.success}; Issues={ctx.last_reflection.issues}; Improvement={ctx.last_reflection.improvement}",
                    metadata={"reflection": ctx.last_reflection.model_dump(mode="json")},
                )
                ctx.steps_taken += 1
                return not ctx.last_reflection.success and not ctx.is_exhausted()

            # Execute tool
            results = self.tool_executor.execute(
                agent_id=ctx.request.agent_id,
                task_id=ctx.request.task_id,
                tool_calls=[tool_call],
                metadata=ctx.request.metadata,
                logs=ctx.logs,
            )
            if not results:
                ctx.error = "Tool execution returned no result"
                return False

            tool_result = results[0]
            ctx.last_tool_call = tool_call
            ctx.tool_calls.append(tool_call)
            ctx.last_tool_result = tool_result
            ctx.tool_results.append(tool_result)
            ctx.steps_taken += 1

            # Observe: add to memory
            ctx.memory.add(
                role="tools",
                content=f"{tool_call.tool_name}.{tool_call.action}: success={tool_result.get('success', False)}",
                metadata={"tool_call": tool_call.model_dump(mode="json"), "result": tool_result},
            )

            # Accumulate result for reflection
            ctx.accumulated_result = {
                "content": tool_result.get("output", tool_result),
                "raw": tool_result,
                "tool_results_count": len(ctx.tool_results),
            }

            # Reflect
            ctx.last_reflection = self.reflection_service.reflect(
                task=ctx.request.task,
                result=ctx.accumulated_result,
                status="completed" if tool_result.get("success") else "partial",
                tool_results=ctx.tool_results,
                model=ctx.request.model,
            )

            # Update memory with reflection
            ctx.memory.add(
                role="reflection",
                content=f"Success={ctx.last_reflection.success}; Issues={ctx.last_reflection.issues}; Improvement={ctx.last_reflection.improvement}",
                metadata={"reflection": ctx.last_reflection.model_dump(mode="json")},
            )

            self._log(
                ctx.logs,
                stage="loop_step",
                level="info",
                message=f"Step {ctx.steps_taken}: {tool_call.tool_name}.{tool_call.action}",
                details={
                    "step": ctx.steps_taken,
                    "tool": f"{tool_call.tool_name}:{tool_call.action}",
                    "reflection_success": ctx.last_reflection.success,
                },
            )

            return not ctx.is_complete() and not ctx.is_exhausted()

        except Exception as exc:
            ctx.error = str(exc)
            ctx.status = "failed"
            self._log(
                ctx.logs,
                stage="loop_error",
                level="error",
                message="Loop step failed.",
                details={"error": str(exc), "step": ctx.steps_taken},
            )
            self.logger.error("Loop step failed.", error=str(exc), step=ctx.steps_taken)
            return False

    def _log(
        self,
        logs: list[ExecutionLogEntry],
        *,
        stage: str,
        level: str,
        message: str,
        details: dict,
    ) -> None:
        logs.append(
            ExecutionLogEntry(
                stage=stage,
                level=level,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details=details,
            )
        )
