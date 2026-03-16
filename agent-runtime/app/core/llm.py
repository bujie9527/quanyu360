from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from app.core.config import get_settings
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionPlan
from app.core.schemas import LLMResult
from app.core.schemas import PlannedToolCall
from app.core.tool_selector import ToolSelector


class BaseLLMAdapter(ABC):
    provider_name: str

    @abstractmethod
    def plan(self, request: AgentRunRequest, available_tools: list[dict[str, Any]]) -> ExecutionPlan:
        raise NotImplementedError

    @abstractmethod
    def generate_result(
        self,
        request: AgentRunRequest,
        plan: ExecutionPlan,
        tool_results: list[dict[str, Any]],
    ) -> LLMResult:
        raise NotImplementedError


class LLMToolSelectionMixin:
    """Uses ToolSelector (LLM) for tool selection when API key available."""

    def _build_plan_with_tool_selector(
        self,
        request: AgentRunRequest,
        available_tools: list[dict[str, Any]],
    ) -> ExecutionPlan | None:
        """Use ToolSelector to pick tool via LLM. Returns None if fallback needed."""
        selector = ToolSelector()
        call = selector.select(
            task=request.task,
            available_tools=available_tools,
            model=request.model,
        )
        if not call:
            return None
        return ExecutionPlan(
            summary=f"LLM selected tool: {call.tool_name}.{call.action}",
            steps=[
                f"Select tool for task: {call.tool_name}.{call.action}",
                "Execute selected tool and collect output.",
                "Synthesize the final response.",
            ],
            tool_calls=[call],
        )


class HeuristicPlanningMixin:
    def _build_fallback_plan(
        self,
        request: AgentRunRequest,
        available_tools: list[dict[str, Any]],
    ) -> ExecutionPlan:
        task_text = " ".join(
            [
                request.task.title,
                request.task.description or "",
                str(request.task.input_payload),
                request.task.expected_output or "",
            ]
        ).lower()

        planned_calls: list[PlannedToolCall] = []
        if request.tool_calls:
            planned_calls = [
                PlannedToolCall(
                    tool_name=call.tool_name,
                    action=call.action,
                    parameters=call.parameters,
                    project_id=call.project_id,
                    metadata=call.metadata,
                    rationale="Call explicitly requested by upstream orchestrator.",
                )
                for call in request.tool_calls
            ]
        else:
            available_tools_by_name = {tool["name"]: tool for tool in available_tools}

            if "wordpress" in available_tools_by_name and any(keyword in task_text for keyword in ["wordpress", "blog", "article", "publish post", "post update"]):
                action = "update_post" if any(keyword in task_text for keyword in ["update", "edit"]) else "publish_post"
                parameters = (
                    {
                        "post_id": request.task.input_payload.get("post_id", "wp_existing_001"),
                        "title": request.task.input_payload.get("title", request.task.title),
                        "content": request.task.input_payload.get("content", request.task.description or request.task.title),
                        "status": request.task.input_payload.get("status", "draft"),
                        "tags": request.task.input_payload.get("tags", []),
                    }
                    if action == "update_post"
                    else {
                        "title": request.task.input_payload.get("title", request.task.title),
                        "content": request.task.input_payload.get("content", request.task.description or request.task.title),
                        "status": request.task.input_payload.get("status", "draft"),
                        "author": request.task.input_payload.get("author"),
                        "tags": request.task.input_payload.get("tags", []),
                    }
                )
                planned_calls.append(
                    PlannedToolCall(
                        tool_name="wordpress",
                        action=action,
                        parameters=parameters,
                        metadata={"source": "heuristic-planner"},
                        rationale="Task content indicates WordPress publishing work.",
                    )
                )

            if "facebook" in available_tools_by_name and any(keyword in task_text for keyword in ["facebook", "social", "comment", "share", "page post"]):
                action = "comment_post" if "comment" in task_text else "create_post"
                parameters = (
                    {
                        "post_id": request.task.input_payload.get("facebook_post_id", "fb_post_001"),
                        "message": request.task.input_payload.get("message", request.task.description or request.task.title),
                    }
                    if action == "comment_post"
                    else {
                        "page_id": request.task.input_payload.get("page_id", "demo_page"),
                        "message": request.task.input_payload.get("message", request.task.description or request.task.title),
                        "link": request.task.input_payload.get("link"),
                    }
                )
                planned_calls.append(
                    PlannedToolCall(
                        tool_name="facebook",
                        action=action,
                        parameters=parameters,
                        metadata={"source": "heuristic-planner"},
                        rationale="Task content indicates Facebook distribution work.",
                    )
                )

        steps = [
            "Analyze task goal and output requirements.",
            "Select the minimum necessary tools.",
            "Execute selected tools and collect outputs." if planned_calls else "No external tools are required for this task.",
            "Synthesize the final response.",
        ]
        return ExecutionPlan(
            summary="Heuristic execution plan generated by runtime planner.",
            steps=steps,
            tool_calls=planned_calls,
        )

    def _build_fallback_result(
        self,
        provider: str,
        model: str,
        request: AgentRunRequest,
        plan: ExecutionPlan,
        tool_results: list[dict[str, Any]],
    ) -> LLMResult:
        content = (
            f"Task '{request.task.title}' executed using provider '{provider}'. "
            f"Planned {len(plan.tool_calls)} tool call(s) and collected {len(tool_results)} tool result(s)."
        )
        return LLMResult(
            provider=provider,
            model=model,
            content=content,
            raw={
                "mode": "fallback",
                "plan_summary": plan.summary,
                "tool_results_count": len(tool_results),
            },
        )


class OpenAIAdapter(LLMToolSelectionMixin, HeuristicPlanningMixin, BaseLLMAdapter):
    provider_name = "openai"

    def plan(self, request: AgentRunRequest, available_tools: list[dict[str, Any]]) -> ExecutionPlan:
        settings = get_settings()
        if settings.openai_api_key and available_tools:
            plan = self._build_plan_with_tool_selector(request, available_tools)
            if plan:
                return plan
        return self._build_fallback_plan(request, available_tools)

    def generate_result(
        self,
        request: AgentRunRequest,
        plan: ExecutionPlan,
        tool_results: list[dict[str, Any]],
    ) -> LLMResult:
        settings = get_settings()
        if not settings.openai_api_key:
            return self._build_fallback_result(self.provider_name, request.model or settings.default_model, request, plan, tool_results)
        return self._build_fallback_result(self.provider_name, request.model or settings.default_model, request, plan, tool_results)


class ClaudeAdapter(LLMToolSelectionMixin, HeuristicPlanningMixin, BaseLLMAdapter):
    provider_name = "claude"

    def plan(self, request: AgentRunRequest, available_tools: list[dict[str, Any]]) -> ExecutionPlan:
        settings = get_settings()
        if settings.claude_api_key and available_tools:
            plan = self._build_plan_with_tool_selector(request, available_tools)
            if plan:
                return plan
        return self._build_fallback_plan(request, available_tools)

    def generate_result(
        self,
        request: AgentRunRequest,
        plan: ExecutionPlan,
        tool_results: list[dict[str, Any]],
    ) -> LLMResult:
        settings = get_settings()
        if not settings.claude_api_key:
            return self._build_fallback_result(self.provider_name, request.model or settings.default_model, request, plan, tool_results)
        return self._build_fallback_result(self.provider_name, request.model or settings.default_model, request, plan, tool_results)


class LocalModelAdapter(HeuristicPlanningMixin, BaseLLMAdapter):
    provider_name = "local"

    def plan(self, request: AgentRunRequest, available_tools: list[dict[str, Any]]) -> ExecutionPlan:
        # Local model has no API; use heuristic only
        return self._build_fallback_plan(request, available_tools)

    def generate_result(
        self,
        request: AgentRunRequest,
        plan: ExecutionPlan,
        tool_results: list[dict[str, Any]],
    ) -> LLMResult:
        settings = get_settings()
        return self._build_fallback_result(self.provider_name, request.model or settings.default_model, request, plan, tool_results)


def resolve_llm_adapter(model_name: str | None) -> BaseLLMAdapter:
    model = (model_name or get_settings().default_model).lower()
    if model.startswith("gpt") or model.startswith("openai"):
        return OpenAIAdapter()
    if model.startswith("claude") or model.startswith("anthropic"):
        return ClaudeAdapter()
    return LocalModelAdapter()
