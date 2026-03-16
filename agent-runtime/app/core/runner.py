"""Agent runtime engine: Task → Planning → Tool Selection → Tool Execution → Result."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone

import structlog

from app.core.analytics import estimate_token_count
from app.core.agent_run_client import ingest_agent_run
from app.core.audit_client import log_agent_run
from common.app.usage_client import track_llm_tokens
from common.app.core.logging import EVENT_AGENT_EXECUTION
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import log_event
from app.core.analytics import record_runtime_execution
from app.core.agent_memory import AgentMemorySystem
from app.core.config import get_settings
from app.core.llm import resolve_llm_adapter
from app.core.memory_manager import MemoryManager
from app.core.schemas import AgentExecutionResult
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import MemoryContext
from app.core.reflection_service import ReflectionService
from app.core.task_planner import TaskPlanner
from app.core.tool_executor import ToolExecutor


def _format_memory_context_for_prompt(ctx: MemoryContext) -> str:
    """Format MemoryContext into a string for injection into system/memory."""
    parts: list[str] = []
    if ctx.relevant_memories:
        mem_strs = [m.get("content", "")[:300] for m in ctx.relevant_memories if m.get("content")]
        if mem_strs:
            parts.append("Relevant past context:\n" + "\n".join(f"- {s}" for s in mem_strs))
    if ctx.recent_turns:
        turns_strs = [f"{t.role}: {t.content[:200]}..." if len(t.content) > 200 else f"{t.role}: {t.content}" for t in ctx.recent_turns[-5:]]
        if turns_strs:
            parts.append("Recent conversation:\n" + "\n".join(turns_strs))
    return "\n\n".join(parts) if parts else ""


class AgentRunner:
    """Main orchestrator: Task → planning → tool selection → tool execution → result."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="agent-runner")
        self.task_planner = TaskPlanner()
        self.tool_executor = ToolExecutor()
        self.reflection_service = ReflectionService()
        self.memory_manager = MemoryManager()
        self.agent_memory = AgentMemorySystem()

    def run(self, request: AgentRunRequest) -> AgentExecutionResult:
        """
        Execution flow:
        1. Task received
        2. Planning (task analysis + tool selection)
        3. Tool execution
        4. Result generation
        5. Memory persistence
        """
        started_at = datetime.now(timezone.utc)
        logs: list[ExecutionLogEntry] = []
        memory = self.memory_manager.create_session(request.agent_id, request.task_id)
        adapter = resolve_llm_adapter(request.model)

        query_text = f"{request.task.title} {request.task.description or ''}".strip()
        past_reflections = request.metadata.get("past_reflections") or []
        if past_reflections and isinstance(past_reflections, list):
            ref_str = "\n".join(
                f"- Success: {r.get('success', True)}; Issues: {r.get('issues', [])}; Improvement: {r.get('improvement', '')}"
                for r in past_reflections[:5]
                if isinstance(r, dict)
            )
            if ref_str:
                memory.add(
                    role="system",
                    content=f"Past self-evaluations to improve this run:\n{ref_str}",
                    metadata={"source": "past_reflections", "stage": "reflection_context"},
                )
        memory_ctx = self.agent_memory.retrieve_context(
            agent_id=request.agent_id,
            query=query_text or None,
            task_id=request.task_id,
        )
        if memory_ctx.recent_turns or memory_ctx.relevant_memories:
            ctx_str = _format_memory_context_for_prompt(memory_ctx)
            if ctx_str:
                memory.add(
                    role="system",
                    content=f"Past context for this agent:\n{ctx_str}",
                    metadata={"source": "agent_memory", "stage": "context_injection"},
                )

        _tid = request.metadata.get("tenant_id") if isinstance(request.metadata.get("tenant_id"), str) else None
        if _tid and self.settings.admin_service_url:
            from common.app.quota_client import check_quota
            from fastapi import HTTPException
            allowed, err = check_quota(self.settings.admin_service_url, tenant_id=_tid, resource="llm_requests_per_month")
            if not allowed:
                raise HTTPException(status_code=429, detail=err or "LLM requests quota exceeded for this month.")

        log_event(
            self.settings.service_name,
            EVENT_AGENT_EXECUTION,
            message="Agent execution started",
            agent_id=request.agent_id,
            task_id=request.task_id,
            task_title=request.task.title,
            model=request.model or self.settings.default_model,
            stage="start",
        )
        self._log(
            logs,
            stage="task_received",
            level="info",
            message="Agent runtime received task.",
            details={
                "agent_id": request.agent_id,
                "task_id": request.task_id,
                "task_title": request.task.title,
                "model": request.model or self.settings.default_model,
            },
        )
        memory.add(
            role="system",
            content=f"Received task '{request.task.title}'.",
            metadata={"task_id": request.task_id},
        )

        try:
            plan = self.task_planner.plan(request, logs)
            memory.add(
                role="planner",
                content=plan.summary,
                metadata={
                    "steps": plan.steps,
                    "tool_calls": [c.model_dump(mode="json") for c in plan.tool_calls],
                },
            )

            tool_results = self.tool_executor.execute(
                agent_id=request.agent_id,
                task_id=request.task_id,
                tool_calls=plan.tool_calls,
                metadata=request.metadata,
                logs=logs,
            )
            memory.add(
                role="tools",
                content=f"Executed {len(tool_results)} tool call(s).",
                metadata={"results": tool_results},
            )

            final_result = adapter.generate_result(request, plan, tool_results)
            self._log(
                logs,
                stage="result_generation",
                level="info",
                message="Final result generated.",
                details={
                    "agent_id": request.agent_id,
                    "task_id": request.task_id,
                    "provider": final_result.provider,
                    "model": final_result.model,
                },
            )
            memory.add(
                role="assistant",
                content=final_result.content,
                metadata=final_result.raw,
            )

            usage = {
                "prompt_tokens": estimate_token_count(
                    request.system_prompt,
                    request.task.title,
                    request.task.description,
                    request.task.input_payload,
                    request.metadata,
                    [c.model_dump(mode="json") for c in plan.tool_calls],
                ),
                "completion_tokens": estimate_token_count(
                    final_result.content, final_result.raw, tool_results
                ),
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

            self.memory_manager.persist(memory, logs)
            completed_at = datetime.now(timezone.utc)
            reflection = self.reflection_service.reflect(
                task=request.task,
                result={"content": final_result.content, "raw": final_result.raw},
                status="completed",
                tool_results=tool_results,
                model=request.model,
            )
            self.agent_memory.update_after_task(
                agent_id=request.agent_id,
                task_id=request.task_id,
                execution_result=AgentExecutionResult(
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                    model=request.model or self.settings.default_model,
                    provider=adapter.provider_name,
                    status="completed",
                    plan=plan,
                    tool_results=tool_results,
                    memory=memory.list(),
                    logs=logs,
                    result={"content": final_result.content, "raw": final_result.raw},
                    reflection=reflection,
                    usage=usage,
                    started_at=started_at,
                    completed_at=completed_at,
                ),
            )
            duration_seconds = (completed_at - started_at).total_seconds()
            self._log(
                logs,
                stage="execution_complete",
                level="info",
                message="Agent execution completed successfully.",
                details={
                    "agent_id": request.agent_id,
                    "task_id": request.task_id,
                    "status": "completed",
                    "duration_ms": round(duration_seconds * 1000, 2),
                    "total_tokens": usage["total_tokens"],
                },
            )
            log_event(
                self.settings.service_name,
                EVENT_AGENT_EXECUTION,
                message="Agent execution completed",
                agent_id=request.agent_id,
                task_id=request.task_id,
                status="completed",
                duration_ms=round(duration_seconds * 1000, 2),
                stage="finish",
            )
            self.logger.info(
                "Execution completed.",
                agent_id=request.agent_id,
                task_id=request.task_id,
                status="completed",
                duration_ms=round(duration_seconds * 1000, 2),
                stage="execution",
            )

            self._record_metrics_safely(
                status="completed",
                provider=adapter.provider_name,
                model=request.model or self.settings.default_model,
                duration_seconds=duration_seconds,
                prompt_tokens=usage["prompt_tokens"],
                completion_tokens=usage["completion_tokens"],
            )
            _tid = request.metadata.get("tenant_id") if isinstance(request.metadata.get("tenant_id"), str) else None
            _pid = request.metadata.get("project_id") if isinstance(request.metadata.get("project_id"), str) else None
            if _tid and self.settings.admin_service_url and (usage.get("prompt_tokens") or usage.get("completion_tokens")):
                track_llm_tokens(
                    self.settings.admin_service_url,
                    tenant_id=_tid,
                    project_id=_pid,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    model=request.model or self.settings.default_model,
                    provider=adapter.provider_name,
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                )
            _pid = request.metadata.get("project_id") if isinstance(request.metadata.get("project_id"), str) else None
            if _tid and self.settings.admin_service_url:
                log_agent_run(
                    self.settings.admin_service_url,
                    tenant_id=_tid,
                    project_id=_pid,
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                    status="completed",
                    correlation_id=request.task_id,
                    payload={"duration_ms": round(duration_seconds * 1000, 2), "usage": usage},
                )
            ingest_agent_run(
                self.settings.agent_service_url,
                agent_id=request.agent_id,
                run_type=request.metadata.get("run_type") or "chat",
                input_payload={
                    "task": {"title": request.task.title, "description": request.task.description, "input_payload": request.task.input_payload},
                    "metadata": request.metadata,
                    "task_id": request.task_id,
                },
                output_payload={
                    "result": {"content": final_result.content, "raw": final_result.raw},
                    "usage": usage,
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
                status="success",
            )
            return AgentExecutionResult(
                agent_id=request.agent_id,
                task_id=request.task_id,
                model=request.model or self.settings.default_model,
                provider=adapter.provider_name,
                status="completed",
                plan=plan,
                tool_results=tool_results,
                memory=memory.list(),
                logs=logs,
                result={"content": final_result.content, "raw": final_result.raw},
                reflection=reflection,
                usage=usage,
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            duration_seconds = (completed_at - started_at).total_seconds()
            _tid = request.metadata.get("tenant_id") if isinstance(request.metadata.get("tenant_id"), str) else None
            _pid = request.metadata.get("project_id") if isinstance(request.metadata.get("project_id"), str) else None
            if _tid and self.settings.admin_service_url:
                track_llm_tokens(
                    self.settings.admin_service_url,
                    tenant_id=_tid,
                    project_id=_pid,
                    prompt_tokens=estimate_token_count(
                        request.system_prompt,
                        request.task.title,
                        request.task.description,
                        request.task.input_payload,
                        request.metadata,
                    ),
                    completion_tokens=0,
                    model=request.model or self.settings.default_model,
                    provider=adapter.provider_name,
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                )
                log_agent_run(
                    self.settings.admin_service_url,
                    tenant_id=_tid,
                    project_id=_pid,
                    agent_id=request.agent_id,
                    task_id=request.task_id,
                    status="failed",
                    correlation_id=request.task_id,
                    payload={"error": str(exc), "duration_ms": round(duration_seconds * 1000, 2)},
                )
            ingest_agent_run(
                self.settings.agent_service_url,
                agent_id=request.agent_id,
                run_type=request.metadata.get("run_type") or "chat",
                input_payload={
                    "task": {"title": request.task.title, "description": request.task.description, "input_payload": request.task.input_payload},
                    "metadata": request.metadata,
                    "task_id": request.task_id,
                },
                output_payload={"error": str(exc), "duration_ms": round(duration_seconds * 1000, 2)},
                status="failed",
            )
            self._log(
                logs,
                stage="execution_failed",
                level="error",
                message="Agent runtime execution failed.",
                details={
                    "agent_id": request.agent_id,
                    "task_id": request.task_id,
                    "error": str(exc),
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
            )
            log_event(
                self.settings.service_name,
                EVENT_AGENT_EXECUTION,
                level="error",
                message="Agent execution failed",
                agent_id=request.agent_id,
                task_id=request.task_id,
                status="failed",
                error=str(exc),
                duration_ms=round(duration_seconds * 1000, 2),
                stage="finish",
            )
            log_event(
                self.settings.service_name,
                EVENT_ERROR,
                level="error",
                message=str(exc),
                agent_id=request.agent_id,
                task_id=request.task_id,
                error=str(exc),
            )
            self.logger.error(
                "Execution failed.",
                agent_id=request.agent_id,
                task_id=request.task_id,
                error=str(exc),
                duration_ms=round(duration_seconds * 1000, 2),
                stage="execution",
            )
            self._record_metrics_safely(
                status="failed",
                provider=adapter.provider_name,
                model=request.model or self.settings.default_model,
                duration_seconds=duration_seconds,
                prompt_tokens=estimate_token_count(
                    request.system_prompt,
                    request.task.title,
                    request.task.description,
                    request.task.input_payload,
                    request.metadata,
                ),
                completion_tokens=0,
            )
            raise

    def _log(
        self,
        logs: list[ExecutionLogEntry],
        *,
        stage: str,
        level: str,
        message: str,
        details: dict,
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
        getattr(self.logger, level, self.logger.info)(message, stage=stage, **details)

    def _record_metrics_safely(
        self,
        *,
        status: str,
        provider: str,
        model: str,
        duration_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        try:
            record_runtime_execution(
                status=status,
                provider=provider,
                model=model,
                duration_seconds=duration_seconds,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception as exc:
            self.logger.warning(
                "Failed to record runtime analytics.",
                status=status,
                provider=provider,
                error=str(exc),
                stage="analytics",
            )


def build_execution(request: AgentRunRequest) -> AgentExecutionResult:
    """Entry point: build and run agent execution."""
    return AgentRunner().run(request)
