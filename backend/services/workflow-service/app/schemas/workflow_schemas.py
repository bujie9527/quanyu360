"""Workflow request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from common.app.models import WorkflowStatus
from common.app.models import WorkflowStepType
from common.app.models import WorkflowTriggerType


# --- Workflow Builder (nodes + edges) ---

class WorkflowNodeInput(BaseModel):
    """Node in workflow builder graph."""
    id: str = Field(min_length=1, max_length=120, description="Unique node id")
    type: str = Field(description="agent_node | tool_node | condition_node | delay_node")
    data: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] | None = Field(default=None, description="UI position {x, y}")


class WorkflowEdgeInput(BaseModel):
    """Edge connecting two nodes."""
    model_config = {"populate_by_name": True}

    id: str | None = Field(default=None, max_length=120)
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    source_handle: str | None = Field(default=None, alias="sourceHandle")
    target_handle: str | None = Field(default=None, alias="targetHandle")


class TriggerScheduleConfig(BaseModel):
    """Schedule trigger: cron expression. Example: '0 9 * * *' = daily at 9am."""
    cron: str = Field(default="0 9 * * *", description="Cron expression (5 fields)")

class TriggerWebhookConfig(BaseModel):
    """Webhook trigger: path for incoming requests."""
    path: str = Field(default="", description="Webhook path, e.g. 'daily-digest' or 'incoming'")

class TriggerEventConfig(BaseModel):
    """Event trigger: when source fires event. Example: blog.created."""
    source: str = Field(default="", description="Event source, e.g. 'blog'")
    event: str = Field(default="", description="Event name, e.g. 'created'")

class WorkflowTriggerConfig(BaseModel):
    """Trigger-specific configuration based on trigger_type."""
    schedule: TriggerScheduleConfig | None = None
    webhook: TriggerWebhookConfig | None = None
    event: TriggerEventConfig | None = None

class WorkflowConfigurationInput(BaseModel):
    """Top-level workflow configuration."""
    trigger_type: str = "manual"
    trigger_config: WorkflowTriggerConfig | None = Field(default=None, description="Config for schedule/webhook/event triggers")
    entry_node_id: str | None = Field(default=None, description="Starting node; defaults to first by edges")
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowBuilderCreateRequest(BaseModel):
    """Create workflow from builder format (nodes, edges, configuration)."""
    project_id: UUID
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=120)
    status: WorkflowStatus = WorkflowStatus.draft
    nodes: list[WorkflowNodeInput] = Field(min_length=1)
    edges: list[WorkflowEdgeInput] = Field(default_factory=list)
    configuration: WorkflowConfigurationInput = Field(default_factory=WorkflowConfigurationInput)

    @field_validator("name")
    @classmethod
    def normalize_name_builder(cls, value: str) -> str:
        return value.strip()


class WorkflowNodeResponse(BaseModel):
    """Node in workflow response."""
    id: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] | None = None


class WorkflowEdgeResponse(BaseModel):
    """Edge in workflow response."""
    model_config = {"populate_by_name": True}

    id: str | None = None
    source: str
    target: str
    source_handle: str | None = Field(default=None, alias="sourceHandle")
    target_handle: str | None = Field(default=None, alias="targetHandle")


class WorkflowConfigurationResponse(BaseModel):
    """Configuration in workflow response."""
    trigger_type: str = "manual"
    trigger_config: dict[str, Any] | None = Field(default=None, description="Schedule/webhook/event config")
    entry_node_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRequest(BaseModel):
    """Request body for workflow run."""
    workflow_id: UUID = Field(description="Workflow to execute")
    input_payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowBuilderDetailResponse(BaseModel):
    """Workflow detail in builder format (nodes, edges, configuration)."""
    id: UUID
    project_id: UUID
    name: str
    slug: str
    version: int
    status: str
    nodes: list[WorkflowNodeResponse]
    edges: list[WorkflowEdgeResponse]
    configuration: WorkflowConfigurationResponse
    created_at: datetime
    updated_at: datetime


def _node_type_to_step_type(node_type: str) -> WorkflowStepType:
    """Map builder node type to WorkflowStepType."""
    m = {
        "agent_node": WorkflowStepType.agent_task,
        "tool_node": WorkflowStepType.tool_call,
        "condition_node": WorkflowStepType.condition,
        "delay_node": WorkflowStepType.delay,
    }
    return m.get(node_type, WorkflowStepType.agent_task)


class WorkflowStepInput(BaseModel):
    step_key: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=255)
    type: WorkflowStepType
    config: dict[str, object] = Field(default_factory=dict)
    next_step: str | None = Field(default=None, max_length=120)
    assigned_agent_id: UUID | None = None
    tool_id: UUID | None = None
    retry_limit: int = Field(default=0, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=1, le=86400)

    @field_validator("step_key", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class WorkflowCreateRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=120)
    status: WorkflowStatus = WorkflowStatus.draft
    trigger_type: WorkflowTriggerType = WorkflowTriggerType.manual
    definition: dict[str, object] = Field(default_factory=dict)
    steps: list[WorkflowStepInput] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class WorkflowUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    status: WorkflowStatus | None = None
    trigger_type: WorkflowTriggerType | None = None
    definition: dict[str, object] | None = None
    steps: list[WorkflowStepInput] | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class WorkflowExecutionRequest(BaseModel):
    input_payload: dict[str, object] = Field(default_factory=dict)
    task_run_id: str | None = Field(default=None, description="Reuse existing TaskRun (e.g. from site building)")


class WorkflowWebhookInvokeRequest(BaseModel):
    """Request body for webhook trigger (optional; body is also used as input_payload)."""
    input_payload: dict[str, object] = Field(default_factory=dict)


class WorkflowEventTriggerRequest(BaseModel):
    """Request body for event trigger."""
    source: str = Field(min_length=1, description="Event source, e.g. 'blog'")
    event: str = Field(min_length=1, description="Event name, e.g. 'created'")
    payload: dict[str, object] = Field(default_factory=dict, description="Event payload as input_payload")


class WorkflowStepResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    step_key: str
    name: str
    type: str
    config: dict[str, object]
    next_step: str | None
    sequence: int
    retry_limit: int
    timeout_seconds: int
    assigned_agent_id: UUID | None
    tool_id: UUID | None


class WorkflowSummaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    version: int
    status: str
    trigger_type: str
    step_count: int
    created_at: datetime
    updated_at: datetime


class WorkflowDetailResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    version: int
    status: str
    trigger_type: str
    definition: dict[str, object]
    steps: list[WorkflowStepResponse]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: UUID
    status: str


class WorkflowListResponse(BaseModel):
    items: list[WorkflowSummaryResponse]
    total: int
