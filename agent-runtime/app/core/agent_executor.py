"""AgentExecutor: full execution loop with plan → select → execute → observe → reflect → memory."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.agent_loop import AgentLoop
from app.core.config import get_settings
from app.core.execution_context import ExecutionContext
from app.core.memory_manager import MemoryManager
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import ExecutionPlan
from app.core.schemas import PlannedToolCall
from app.core.schemas import Reflection
from app.core.tooling import list_registered_tools
from common.app.core.logging import EVENT_AGENT_EXECUTION
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import log_event


class AgentExecutor:
    """
    Full agent execution loop with safety limits.
    while not task_complete:
      plan → select tool → execute → observe → reflect → update memory
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="agent-executor")
        self.agent_loop = AgentLoop()
        self.memory_manager = MemoryManager()

    def execute(
        self,
        request: AgentRunRequest,
        *,
        max_steps: int | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """
        Run the full agent loop until complete or limits reached.
        Returns execution summary compatible with AgentExecutionResult.
        """
        max_steps = max_steps or self.settings.agent_loop_max_steps
        timeout_seconds = timeout_seconds or self.settings.agent_loop_timeout_seconds

        _tid = request.metadata.get("tenant_id") if isinstance(request.metadata.get("tenant_id"), str) else None
        if _tid and self.settings.admin_service_url:
            from common.app.quota_client import check_quota
            from fastapi import HTTPException
            allowed, err = check_quota(self.settings.admin_service_url, tenant_id=_tid, resource="llm_requests_per_month")
            if not allowed:
                raise HTTPException(status_code=429, detail=err or "LLM requests quota exceeded for this month.")

        started_at = datetime.now(timezone.utc)
        memory = self.memory_manager.create_session(request.agent_id, request.task_id)
        logs: list[ExecutionLogEntry] = []

        ctx = ExecutionContext(
            request=request,
            memory=memory,
            logs=logs,
            started_at=started_at,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
        )

        # Initial plan (high-level) - add to memory
        memory.add(
            role="system",
            content=f"Task: {request.task.title}. {request.task.description or ''}",
            metadata={"stage": "init"},
        )

        log_event(
            self.settings.service_name,
            EVENT_AGENT_EXECUTION,
            message="Agent executor loop started",
            agent_id=request.agent_id,
            task_id=request.task_id,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
            stage="start",
        )

        try:
            while not ctx.is_complete() and not ctx.is_exhausted():
                should_continue = self.agent_loop.step(ctx)
                if not should_continue:
                    break

            completed_at = datetime.now(timezone.utc)
            duration_seconds = (completed_at - started_at).total_seconds()

            # Persist memory
            self.memory_manager.persist(memory, logs)

            status = "completed" if ctx.last_reflection and ctx.last_reflection.success and not ctx.error else "failed"
            if ctx.error:
                status = "failed"
                log_event(
                    self.settings.service_name,
                    EVENT_ERROR,
                    level="error",
                    message=ctx.error,
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                )

            # Build ExecutionPlan from tool calls for compatibility
            plan = ExecutionPlan(
                summary=f"Loop completed after {ctx.steps_taken} steps.",
                steps=[f"Step {i+1}" for i in range(ctx.steps_taken)],
                tool_calls=ctx.tool_calls,
            )

            self.logger.info(
                "Agent executor loop finished.",
                agent_id=request.agent_id,
                task_id=request.task_id,
                status=status,
                steps=ctx.steps_taken,
                duration_seconds=round(duration_seconds, 2),
            )

            return {
                "agent_id": request.agent_id,
                "task_id": request.task_id,
                "model": request.model or self.settings.default_model,
                "provider": "agent-executor",
                "status": status,
                "plan": plan.model_dump(mode="json"),
                "tool_results": ctx.tool_results,
                "memory": [e.model_dump(mode="json") for e in memory.list()],
                "logs": [e.model_dump(mode="json") for e in logs],
                "result": ctx.accumulated_result or {},
                "reflection": ctx.last_reflection.model_dump(mode="json") if ctx.last_reflection else None,
                "usage": {"steps": ctx.steps_taken},
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "error": ctx.error,
            }

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            ctx.error = str(exc)
            ctx.status = "failed"
            log_event(
                self.settings.service_name,
                EVENT_ERROR,
                level="error",
                message=str(exc),
                agent_id=request.agent_id,
                task_id=request.task_id,
            )
            self.logger.error("Agent executor failed.", error=str(exc))
            return {
                "agent_id": request.agent_id,
                "task_id": request.task_id,
                "model": request.model or self.settings.default_model,
                "provider": "agent-executor",
                "status": "failed",
                "plan": {"summary": str(exc), "steps": [], "tool_calls": []},
                "tool_results": ctx.tool_results,
                "memory": [e.model_dump(mode="json") for e in memory.list()],
                "logs": [e.model_dump(mode="json") for e in logs],
                "result": {},
                "reflection": None,
                "usage": {"steps": ctx.steps_taken},
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "error": str(exc),
            }
