from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class NodeType(str, Enum):
    """Supported workflow node types."""
    agent_node = "agent_node"
    tool_node = "tool_node"
    condition_node = "condition_node"
    delay_node = "delay_node"


# Legacy step type → node type mapping
_STEP_TYPE_TO_NODE: dict[str, str] = {
    "agent_task": NodeType.agent_node.value,
    "tool_call": NodeType.tool_node.value,
    "condition": NodeType.condition_node.value,
    "delay": NodeType.delay_node.value,
}


def normalize_node_type(step_type: str) -> str:
    """Map legacy step types to node types."""
    return _STEP_TYPE_TO_NODE.get(step_type, step_type)


class WorkflowNode(BaseModel):
    """A workflow node (refactored from step)."""
    id: str
    workflow_id: str
    node_key: str
    name: str
    node_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    next_node: str | None = None
    sequence: int
    retry_limit: int = 0
    timeout_seconds: int = 300
    assigned_agent_id: str | None = None
    tool_id: str | None = None

    @classmethod
    def from_step(cls, step: dict[str, Any]) -> "WorkflowNode":
        """Build from legacy step dict or node dict."""
        node_type = step.get("node_type") or normalize_node_type(str(step.get("type", "agent_task")))
        return cls(
            id=str(step.get("id", "")),
            workflow_id=str(step.get("workflow_id", "")),
            node_key=str(step.get("step_key", step.get("node_key", ""))),
            name=str(step.get("name", "")),
            node_type=str(node_type),
            config=step.get("config") or {},
            next_node=step.get("next_step") or step.get("next_node"),
            sequence=int(step.get("sequence", 0)),
            retry_limit=int(step.get("retry_limit", 0)),
            timeout_seconds=int(step.get("timeout_seconds", 300)),
            assigned_agent_id=step.get("assigned_agent_id"),
            tool_id=step.get("tool_id"),
        )


class EngineStep(BaseModel):
    """Legacy schema; maps to WorkflowNode."""
    id: str
    workflow_id: str
    step_key: str
    name: str
    type: str
    config: dict[str, Any] = Field(default_factory=dict)
    next_step: str | None = None
    sequence: int
    retry_limit: int = 0
    timeout_seconds: int = 300
    assigned_agent_id: str | None = None
    tool_id: str | None = None


class EngineWorkflowSnapshot(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    version: int
    status: str
    trigger_type: str
    definition: dict[str, Any] = Field(default_factory=dict)
    steps: list[EngineStep] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)


class ExecutionCreateRequest(BaseModel):
    workflow_id: str
    workflow: EngineWorkflowSnapshot
    input_payload: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    task_run_id: str | None = None


class StepExecutionRecord(BaseModel):
    step_key: str
    step_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    next_step: str | None = None
    error_message: str | None = None


class WorkflowExecutionState(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    current_step: str | None = None  # Legacy; same as current_node
    current_node: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    step_history: list[StepExecutionRecord] = Field(default_factory=list)
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class WorkflowExecutionSummary(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    current_step: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class StepExecutionResult(BaseModel):
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    next_step: str | None = None
    error_message: str | None = None
