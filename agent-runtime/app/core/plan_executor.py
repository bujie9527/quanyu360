"""PlanExecutor: executes plan steps in order, delegating to agent/tools as needed."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.schemas import Plan
from app.core.schemas import PlanStep


class StepResult:
    """Result of executing a single plan step."""

    def __init__(
        self,
        step: PlanStep,
        index: int,
        success: bool,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        duration_ms: float = 0,
    ) -> None:
        self.step = step
        self.index = index
        self.success = success
        self.output = output or {}
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "step": self.step.step,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


class PlanExecutor:
    """
    Executes a Plan (list of steps) in order.
    Each step can be delegated to an agent, tool, or handled as a placeholder.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="plan-executor")

    def execute(
        self,
        plan: Plan,
        *,
        agent_id: str | None = None,
        task_id: str | None = None,
        task_context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        stop_on_failure: bool = False,
    ) -> list[StepResult]:
        """
        Execute plan steps in order.
        Currently performs placeholder execution (logs and records); can be extended
        to delegate each step to AgentRunner or tool registry.
        """
        results: list[StepResult] = []
        context = dict(task_context or {})
        metadata = metadata or {}

        self.logger.info(
            "Plan execution started.",
            plan_steps_count=len(plan.steps),
            agent_id=agent_id,
            task_id=task_id,
        )

        for idx, step in enumerate(plan.steps):
            started = datetime.now(timezone.utc)
            try:
                output = self._execute_step(step, idx, context, agent_id, task_id, metadata)
                duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
                results.append(
                    StepResult(
                        step=step,
                        index=idx,
                        success=True,
                        output=output,
                        duration_ms=duration_ms,
                    )
                )
                context[f"step_{idx}_result"] = output
                self.logger.info(
                    "Step executed.",
                    index=idx,
                    step=step.step,
                    success=True,
                    duration_ms=round(duration_ms, 2),
                )
            except Exception as exc:
                duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
                results.append(
                    StepResult(
                        step=step,
                        index=idx,
                        success=False,
                        error=str(exc),
                        duration_ms=duration_ms,
                    )
                )
                self.logger.warning(
                    "Step failed.",
                    index=idx,
                    step=step.step,
                    error=str(exc),
                )
                if stop_on_failure:
                    break

        self.logger.info(
            "Plan execution completed.",
            total_steps=len(plan.steps),
            completed=len([r for r in results if r.success]),
            failed=len([r for r in results if not r.success]),
        )
        return results

    def _execute_step(
        self,
        step: PlanStep,
        index: int,
        context: dict[str, Any],
        agent_id: str | None,
        task_id: str | None,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a single step. Override or extend to integrate with AgentRunner/tools.
        Default: placeholder that records the step intent.
        """
        # Placeholder: record step for later integration with agent/tools
        return {
            "step": step.step,
            "index": index,
            "status": "placeholder",
            "message": f"Step '{step.step}' recorded; delegate to agent/tools for real execution.",
        }
