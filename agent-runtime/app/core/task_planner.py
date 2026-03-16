"""Task planning and tool selection component."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.llm import resolve_llm_adapter
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import ExecutionPlan
from app.core.tooling import list_registered_tools


class TaskPlanner:
    """Plans task execution and selects tools based on task requirements."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="task-planner")

    def plan(
        self,
        request: AgentRunRequest,
        logs: list[ExecutionLogEntry],
    ) -> ExecutionPlan:
        """
        Generate an execution plan: analyze task, select tools, produce ordered steps.
        Task → Planning → Tool Selection.
        """
        started_at = datetime.now(timezone.utc)
        allowed_slugs = None
        if isinstance(request.metadata.get("allowed_tool_slugs"), list):
            allowed_slugs = [s for s in request.metadata["allowed_tool_slugs"] if isinstance(s, str)]
        available_tools = list_registered_tools(allowed_slugs=allowed_slugs)
        adapter = resolve_llm_adapter(request.model)

        self._log(
            logs,
            stage="planning_start",
            level="info",
            message="Task planning started.",
            details={
                "agent_id": request.agent_id,
                "task_id": request.task_id,
                "model": request.model or self.settings.default_model,
                "provider": adapter.provider_name,
                "available_tools_count": len(available_tools),
                "tool_names": [t.get("name") for t in available_tools],
            },
        )

        plan = adapter.plan(request, available_tools)

        duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
        self._log(
            logs,
            stage="planning_complete",
            level="info",
            message="Execution plan generated.",
            details={
                "agent_id": request.agent_id,
                "task_id": request.task_id,
                "provider": adapter.provider_name,
                "tool_calls_count": len(plan.tool_calls),
                "steps_count": len(plan.steps),
                "duration_ms": round(duration_ms, 2),
                "selected_tools": [c.tool_name for c in plan.tool_calls],
            },
        )

        return plan

    def _log(
        self,
        logs: list[ExecutionLogEntry],
        *,
        stage: str,
        level: str,
        message: str,
        details: dict[str, Any],
    ) -> None:
        timestamp = datetime.now(timezone.utc)
        logs.append(
            ExecutionLogEntry(
                stage=stage,
                level=level,
                message=message,
                timestamp=timestamp,
                details=details,
            )
        )
        log_fn = getattr(self.logger, level, self.logger.info)
        log_fn(message, stage=stage, **details)
