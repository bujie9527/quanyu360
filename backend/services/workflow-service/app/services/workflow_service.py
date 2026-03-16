"""Workflow business logic."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID

import httpx

from app.config import settings
from app.repositories import TaskRunRepository
from app.repositories import WorkflowRepository
from app.schemas.workflow_schemas import WorkflowCreateRequest
from app.schemas.workflow_schemas import WorkflowExecutionRequest
from app.schemas.workflow_schemas import WorkflowStepInput
from app.schemas.workflow_schemas import WorkflowUpdateRequest
from app.schemas.workflow_schemas import WorkflowBuilderCreateRequest
from app.schemas.workflow_schemas import _node_type_to_step_type
from common.app.models import Workflow
from common.app.models import WorkflowStatus
from common.app.models import WorkflowStep
from common.app.models import WorkflowStepType
from common.app.models import WorkflowTriggerType
from fastapi import HTTPException
from fastapi import status


class WorkflowService:
    """Orchestrates workflow business logic."""

    def __init__(self, repo: WorkflowRepository, task_run_repo: TaskRunRepository | None = None):
        self.repo = repo
        self.task_run_repo = task_run_repo

    def list_workflows(
        self,
        project_id: UUID | None = None,
        status_filter: WorkflowStatus | None = None,
        trigger_type: WorkflowTriggerType | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Workflow], int]:
        return self.repo.list(
            project_id=project_id,
            status_filter=status_filter,
            trigger_type=trigger_type,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_workflow(self, workflow_id: UUID) -> Workflow:
        wf = self.repo.get(workflow_id)
        if wf is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
        return wf

    def create_workflow(self, payload: WorkflowCreateRequest) -> Workflow:
        project = self.repo.get_project(payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        slug = payload.slug or self.repo.generate_slug(payload.project_id, payload.name)
        self._validate_steps(
            payload.project_id, payload.steps, is_draft=payload.status == WorkflowStatus.draft
        )
        workflow = Workflow(
            project_id=project.id,
            name=payload.name,
            slug=slug,
            version=1,
            status=payload.status,
            trigger_type=payload.trigger_type,
            definition=payload.definition,
            published_at=datetime.now(timezone.utc) if payload.status == WorkflowStatus.active else None,
        )
        self.repo.add(workflow)
        self._replace_steps(workflow, payload.steps)
        self.repo.db.commit()
        return self.get_workflow(workflow.id)

    def create_workflow_from_builder(self, payload: WorkflowBuilderCreateRequest) -> Workflow:
        """Create workflow from builder format (nodes, edges, configuration)."""
        project = self.repo.get_project(payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        slug = payload.slug or self.repo.generate_slug(payload.project_id, payload.name)
        steps = self._builder_to_steps(payload)
        self._validate_steps(project.id, steps, is_draft=payload.status == WorkflowStatus.draft)
        trigger = self._parse_trigger_type(payload.configuration.trigger_type)
        workflow = Workflow(
            project_id=project.id,
            name=payload.name,
            slug=slug,
            version=1,
            status=payload.status,
            trigger_type=trigger,
            definition={
                "nodes": [n.model_dump(mode="json") for n in payload.nodes],
                "edges": [e.model_dump(mode="json", by_alias=True) for e in payload.edges],
                "configuration": payload.configuration.model_dump(mode="json"),
            },
            published_at=datetime.now(timezone.utc) if payload.status == WorkflowStatus.active else None,
        )
        self.repo.add(workflow)
        self._replace_steps(workflow, steps)
        self.repo.db.commit()
        return self.get_workflow(workflow.id)

    def _parse_trigger_type(self, value: str) -> WorkflowTriggerType:
        try:
            return WorkflowTriggerType(value.lower())
        except ValueError:
            return WorkflowTriggerType.manual

    def _builder_to_steps(self, payload: WorkflowBuilderCreateRequest) -> list[WorkflowStepInput]:
        """Convert nodes + edges to WorkflowStepInput list with topological order."""
        node_by_id = {n.id: n for n in payload.nodes}
        out_edges: dict[str, list[str]] = {}
        in_degree: dict[str, int] = {n.id: 0 for n in payload.nodes}
        for e in payload.edges:
            if e.source not in out_edges:
                out_edges[e.source] = []
            out_edges[e.source].append(e.target)
            in_degree[e.target] = in_degree.get(e.target, 0) + 1
        queue = [nid for nid, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for t in out_edges.get(nid, []):
                in_degree[t] -= 1
                if in_degree[t] == 0:
                    queue.append(t)
        for nid in node_by_id:
            if nid not in order:
                order.append(nid)
        # map node_id -> step_key (ensure min 2 chars for schema)
        node_to_step_key: dict[str, str] = {}
        for seq, nid in enumerate(order, start=1):
            node = node_by_id.get(nid)
            if node:
                sk = nid if len(nid) >= 2 else f"s{nid}"
                node_to_step_key[nid] = sk
        result: list[WorkflowStepInput] = []
        for seq, nid in enumerate(order, start=1):
            node = node_by_id.get(nid)
            if not node:
                continue
            step_key = node_to_step_key[nid]
            target_nid = out_edges.get(nid, [None])[0] if out_edges.get(nid) else None
            next_step = node_to_step_key.get(target_nid) if target_nid else None
            data = node.data or {}
            config = dict(data)
            step_type = _node_type_to_step_type(node.type)
            agent_id = data.get("assigned_agent_id")
            if isinstance(agent_id, str):
                try:
                    agent_id = UUID(agent_id)
                except ValueError:
                    agent_id = None
            elif not isinstance(agent_id, UUID):
                agent_id = None
            tool_id = data.get("tool_id")
            if isinstance(tool_id, str):
                try:
                    tool_id = UUID(tool_id)
                except ValueError:
                    tool_id = None
            elif not isinstance(tool_id, UUID):
                tool_id = None
            raw_name = str(data.get("name", "") or "").strip()
            step_name = raw_name if len(raw_name) >= 2 else (step_key if len(step_key) >= 2 else f"step_{seq}")
            result.append(
                WorkflowStepInput(
                    step_key=step_key,
                    name=step_name,
                    type=step_type,
                    config=config,
                    next_step=next_step,
                    assigned_agent_id=agent_id,
                    tool_id=tool_id,
                    retry_limit=int(data.get("retry_limit", 0)),
                    timeout_seconds=int(data.get("timeout_seconds", 300)),
                )
            )
        return result

    def update_workflow(self, workflow_id: UUID, payload: WorkflowUpdateRequest) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        if "name" in payload.model_fields_set and payload.name is not None:
            workflow.name = payload.name
        if "status" in payload.model_fields_set and payload.status is not None:
            workflow.status = payload.status
            workflow.published_at = datetime.now(timezone.utc) if payload.status == WorkflowStatus.active else None
        if "trigger_type" in payload.model_fields_set and payload.trigger_type is not None:
            workflow.trigger_type = payload.trigger_type
        if "definition" in payload.model_fields_set and payload.definition is not None:
            workflow.definition = payload.definition
        if payload.steps is not None:
            self._validate_steps(
                workflow.project_id, payload.steps, is_draft=workflow.status == WorkflowStatus.draft
            )
            self._replace_steps(workflow, payload.steps)
        self.repo.db.commit()
        return self.get_workflow(workflow.id)

    def delete_workflow(self, workflow_id: UUID) -> None:
        workflow = self.get_workflow(workflow_id)
        self.repo.delete(workflow)
        self.repo.db.commit()

    def execute_workflow_by_webhook(self, path: str, input_payload: dict | None = None) -> dict | None:
        """Execute workflow by webhook path. Returns execution result or None if not found."""
        workflow = self.repo.get_by_webhook_path(path)
        if workflow is None:
            return None
        return self.execute_workflow(workflow.id, WorkflowExecutionRequest(input_payload=input_payload or {}))

    def trigger_workflows_by_event(self, source: str, event: str, payload: dict | None = None) -> list[dict]:
        """Trigger all workflows matching source.event. Returns list of execution results."""
        workflows = self.repo.list_by_event(source, event)
        results = []
        for wf in workflows:
            try:
                r = self.execute_workflow(wf.id, WorkflowExecutionRequest(input_payload=payload or {}))
                results.append(r)
            except Exception:
                pass
        return results

    def list_scheduled_workflows(self) -> list[Workflow]:
        """List active workflows with scheduled trigger for cron scheduler."""
        return self.repo.list_scheduled()

    def execute_workflow(self, workflow_id: UUID, payload: WorkflowExecutionRequest) -> dict:
        workflow = self.get_workflow(workflow_id)
        if workflow.status != WorkflowStatus.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only active workflows can be executed.",
            )
        inp = payload.input_payload or {}
        task_template_id = None
        if isinstance(inp.get("task_template_id"), str):
            try:
                task_template_id = UUID(inp["task_template_id"])
            except (ValueError, TypeError):
                pass

        task_run_id = None
        if payload.task_run_id:
            # Reuse existing TaskRun (e.g. from site building)
            try:
                tr_id = UUID(payload.task_run_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid task_run_id.",
                )
            tr = self.task_run_repo.get(tr_id) if self.task_run_repo else None
            if tr is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="TaskRun not found.",
                )
            if tr.workflow_id != workflow.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TaskRun does not belong to this workflow.",
                )
            task_run_id = str(tr.id)
        elif self.task_run_repo:
            tr = self.task_run_repo.create(
                workflow_id=workflow.id,
                execution_id="",
                task_template_id=task_template_id,
            )
            task_run_id = str(tr.id)
            self.repo.db.commit()

        execution_payload = {
            "workflow_id": str(workflow.id),
            "workflow": self._serialize_workflow_snapshot(workflow),
            "input_payload": payload.input_payload,
            "tenant_id": str(workflow.project.tenant_id) if workflow.project else None,
        }
        if task_run_id:
            execution_payload["task_run_id"] = task_run_id

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{settings.workflow_engine_url}{settings.api_v1_prefix}/executions",
                    json=execution_payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            if task_run_id and self.task_run_repo:
                self.task_run_repo.update_status(
                    UUID(task_run_id), "failed", datetime.now(timezone.utc)
                )
                self.repo.db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Workflow engine unavailable: {exc}",
            ) from exc

        result = response.json()
        if task_run_id and self.task_run_repo and result.get("execution_id"):
            tr = self.task_run_repo.get(UUID(task_run_id))
            if tr:
                tr.execution_id = result["execution_id"]
                self.repo.db.commit()
        return result

    def _replace_steps(self, workflow: Workflow, steps: list[WorkflowStepInput]) -> None:
        for existing in list(workflow.steps):
            self.repo.db.delete(existing)
        self.repo.db.flush()
        for index, step in enumerate(steps, start=1):
            self.repo.db.add(
                WorkflowStep(
                    workflow=workflow,
                    assigned_agent_id=step.assigned_agent_id,
                    tool_id=step.tool_id,
                    step_key=step.step_key,
                    next_step_key=step.next_step,
                    name=step.name,
                    step_type=step.type,
                    sequence=index,
                    retry_limit=step.retry_limit,
                    timeout_seconds=step.timeout_seconds,
                    config=step.config,
                )
            )
        self.repo.db.flush()

    def _validate_steps(
        self, project_id: UUID, steps: list[WorkflowStepInput], *, is_draft: bool = False
    ) -> None:
        step_keys = {s.step_key for s in steps}
        if len(step_keys) != len(steps):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow step keys must be unique.",
            )
        for step in steps:
            if step.next_step is not None and step.next_step not in step_keys:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Workflow step '{step.step_key}' references unknown next step '{step.next_step}'.",
                )
            if not is_draft:
                if step.type == WorkflowStepType.agent_task and step.assigned_agent_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Workflow step '{step.step_key}' requires assigned_agent_id.",
                    )
                if step.type == WorkflowStepType.tool_call:
                    has_tool_id = step.tool_id is not None
                    has_tool_config = bool(
                        step.config
                        and step.config.get("tool_name")
                        and step.config.get("action")
                    )
                    if not has_tool_id and not has_tool_config:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Workflow step '{step.step_key}' requires tool_id or config with tool_name and action.",
                        )
            if step.assigned_agent_id is not None:
                if not self.repo.agent_exists_in_project(step.assigned_agent_id, project_id):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Assigned agent for step '{step.step_key}' was not found in the project.",
                    )
            if step.tool_id is not None:
                if not self.repo.tool_exists_in_project(step.tool_id, project_id):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Assigned tool for step '{step.step_key}' was not found in the project.",
                    )

    @staticmethod
    def _serialize_workflow_snapshot(workflow: Workflow) -> dict[str, object]:
        step_type_to_node = {
            "agent_task": "agent_node",
            "tool_call": "tool_node",
            "condition": "condition_node",
            "delay": "delay_node",
        }
        steps_data = []
        nodes_data = []
        for step in sorted(workflow.steps, key=lambda s: s.sequence):
            step_dict = {
                "id": str(step.id),
                "workflow_id": str(step.workflow_id),
                "step_key": step.step_key,
                "name": step.name,
                "type": step.step_type.value,
                "config": dict(step.config),
                "next_step": step.next_step_key,
                "sequence": step.sequence,
                "retry_limit": step.retry_limit,
                "timeout_seconds": step.timeout_seconds,
                "assigned_agent_id": str(step.assigned_agent_id) if step.assigned_agent_id else None,
                "tool_id": str(step.tool_id) if step.tool_id else None,
            }
            steps_data.append(step_dict)
            node_type = step_type_to_node.get(step.step_type.value, f"{step.step_type.value}_node")
            node_config = dict(step.config)
            if step.assigned_agent_id:
                node_config.setdefault("agent_id", str(step.assigned_agent_id))
                node_config.setdefault("assigned_agent_id", str(step.assigned_agent_id))
            if step.tool_id and step.tool:
                node_config.setdefault("tool_name", step.tool.slug)
            node_dict = {
                "id": str(step.id),
                "workflow_id": str(step.workflow_id),
                "node_key": step.step_key,
                "step_key": step.step_key,
                "name": step.name,
                "type": step.step_type.value,
                "node_type": node_type,
                "config": node_config,
                "next_step": step.next_step_key,
                "next_node": step.next_step_key,
                "sequence": step.sequence,
                "retry_limit": step.retry_limit,
                "timeout_seconds": step.timeout_seconds,
                "assigned_agent_id": str(step.assigned_agent_id) if step.assigned_agent_id else None,
                "tool_id": str(step.tool_id) if step.tool_id else None,
            }
            nodes_data.append(node_dict)
        return {
            "id": str(workflow.id),
            "project_id": str(workflow.project_id),
            "name": workflow.name,
            "slug": workflow.slug,
            "version": workflow.version,
            "status": workflow.status.value,
            "trigger_type": workflow.trigger_type.value,
            "definition": workflow.definition,
            "steps": steps_data,
            "nodes": nodes_data,
        }
