from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ToolCallRequestModel(BaseModel):
    tool_name: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    agent_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeTaskPayload(BaseModel):
    title: str
    description: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_output: str | None = None


class AgentRunRequest(BaseModel):
    agent_id: str
    task_id: str
    model: str | None = None
    system_prompt: str | None = None
    task: RuntimeTaskPayload
    tool_calls: list[ToolCallRequestModel] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TeamMemberInput(BaseModel):
    """Member of an agent team for collaboration."""
    agent_id: str
    role_in_team: str
    order_index: int = 0
    model: str | None = None  # Override default model for this agent


class TeamRunRequest(BaseModel):
    """Request to run a multi-agent team."""
    team_id: str
    task_id: str
    execution_type: str = Field(description="sequential | parallel | review_loop")
    members: list[TeamMemberInput] = Field(default_factory=list)
    task: RuntimeTaskPayload
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionLogEntry(BaseModel):
    stage: str
    level: str
    message: str
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    role: str
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    """A single turn in a conversation (user/assistant/system)."""
    role: str
    content: str
    timestamp: datetime
    task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryContext(BaseModel):
    """Retrieved context for agent: recent turns + relevant long-term memories."""
    recent_turns: list[ConversationTurn] = Field(default_factory=list)
    relevant_memories: list[dict[str, Any]] = Field(default_factory=list)


class PlannedToolCall(BaseModel):
    tool_name: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = None


class PlanStep(BaseModel):
    """A single step in an agent execution plan."""

    step: str = Field(min_length=1, max_length=500, description="Short description of the step")


class Plan(BaseModel):
    """LLM-generated plan: ordered list of steps to execute."""

    steps: list[PlanStep] = Field(min_length=1, max_length=50, description="Ordered execution steps")


class PlanRequest(BaseModel):
    """Request body for plan generation."""

    task: RuntimeTaskPayload
    model: str | None = None


class PlanExecuteRequest(BaseModel):
    """Request body for plan-and-execute."""

    task: RuntimeTaskPayload
    agent_id: str | None = None
    task_id: str | None = None
    model: str | None = None
    stop_on_failure: bool = False


class ToolSelectRequest(BaseModel):
    """Request body for tool select / select-and-execute."""

    task: RuntimeTaskPayload
    agent_id: str | None = None
    task_id: str | None = None
    model: str | None = None


class ExecutionPlan(BaseModel):
    summary: str
    steps: list[str] = Field(default_factory=list)
    tool_calls: list[PlannedToolCall] = Field(default_factory=list)


class LLMResult(BaseModel):
    provider: str
    model: str
    content: str
    raw: dict[str, Any] = Field(default_factory=dict)


class Reflection(BaseModel):
    """Agent self-evaluation after task execution."""

    success: bool = Field(description="Whether the execution was successful")
    issues: list[str] = Field(default_factory=list, description="Identified issues")
    improvement: str = Field(default="", description="Suggested improvement for next run")


class AgentExecutionResult(BaseModel):
    agent_id: str
    task_id: str
    model: str
    provider: str
    status: str
    plan: ExecutionPlan
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    memory: list[MemoryEntry] = Field(default_factory=list)
    logs: list[ExecutionLogEntry] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    reflection: Reflection | None = Field(default=None, description="Agent self-evaluation")
    usage: dict[str, int] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime


class MemberRunResult(BaseModel):
    """Result of a single agent run within a team execution."""
    agent_id: str
    role_in_team: str
    order_index: int
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    content: str = ""


class TeamExecutionResult(BaseModel):
    """Result of multi-agent team execution."""
    team_id: str
    task_id: str
    execution_type: str
    status: str = "completed"
    member_results: list[MemberRunResult] = Field(default_factory=list)
    combined_result: dict[str, Any] = Field(default_factory=dict)
    logs: list[ExecutionLogEntry] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime


class AnalyticsPoint(BaseModel):
    label: str
    value: float


class RuntimeAnalyticsSummary(BaseModel):
    runs_total: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    average_execution_time_seconds: float
    prompt_tokens_total: int
    completion_tokens_total: int
    total_tokens_total: int
    average_tokens_per_run: float
    provider_breakdown: list[AnalyticsPoint] = Field(default_factory=list)
    recent_token_usage: list[AnalyticsPoint] = Field(default_factory=list)
    execution_time_breakdown: list[AnalyticsPoint] = Field(default_factory=list)
