"""ExecutionContext: mutable state for agent execution loop."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any

from app.core.memory import RuntimeMemory
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import PlannedToolCall
from app.core.schemas import Reflection
from app.core.schemas import RuntimeTaskPayload


@dataclass
class ExecutionContext:
    """
    Mutable context for agent execution loop.
    Tracks state, observations, and safety limits.
    """

    request: AgentRunRequest
    memory: RuntimeMemory
    logs: list[ExecutionLogEntry]
    started_at: datetime
    max_steps: int = 10
    timeout_seconds: int = 300

    steps_taken: int = 0
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[PlannedToolCall] = field(default_factory=list)
    last_reflection: Reflection | None = None
    last_tool_call: PlannedToolCall | None = None
    last_tool_result: dict[str, Any] | None = None
    error: str | None = None
    status: str = "running"
    accumulated_result: dict[str, Any] = field(default_factory=dict)

    def is_complete(self) -> bool:
        """Task is complete when reflection says success."""
        if self.error:
            return True
        if self.status != "running":
            return True
        if self.last_reflection and self.last_reflection.success:
            return True
        return False

    def is_exhausted(self) -> bool:
        """Safety limits exhausted."""
        if self.steps_taken >= self.max_steps:
            return True
        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        if elapsed >= self.timeout_seconds:
            return True
        if self.error:
            return True
        return False

    def task_for_tool_selection(self) -> RuntimeTaskPayload:
        """Task augmented with observations for tool selection."""
        observations = []
        if self.tool_results:
            observations.append(f"Previous tool results ({len(self.tool_results)}): {self.tool_results[-3:]}")
        if self.last_reflection:
            observations.append(f"Reflection: success={self.last_reflection.success}, improvement={self.last_reflection.improvement}")
        desc = self.request.task.description or ""
        if observations:
            desc = (f"{desc}\n\nObservations:\n" + "\n".join(observations)) if desc else ("Observations:\n" + "\n".join(observations))
        return RuntimeTaskPayload(
            title=self.request.task.title,
            description=desc,
            input_payload=self.request.task.input_payload or {},
            expected_output=self.request.task.expected_output,
        )
