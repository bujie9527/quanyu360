"""Workflow data access layer."""
from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from common.app.models import Agent
from common.app.models import Project
from common.app.models import Tool
from common.app.models import Workflow
from common.app.models import WorkflowStatus
from common.app.models import WorkflowStep
from common.app.models import WorkflowTriggerType


class WorkflowRepository:
    """Handles database access for workflows."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID | None = None,
        status_filter: WorkflowStatus | None = None,
        trigger_type: WorkflowTriggerType | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Workflow], int]:
        statement = self._base_statement()
        count_statement = select(func.count(Workflow.id))
        if project_id is not None:
            statement = statement.where(Workflow.project_id == project_id)
            count_statement = count_statement.where(Workflow.project_id == project_id)
        if status_filter is not None:
            statement = statement.where(Workflow.status == status_filter)
            count_statement = count_statement.where(Workflow.status == status_filter)
        if trigger_type is not None:
            statement = statement.where(Workflow.trigger_type == trigger_type)
            count_statement = count_statement.where(Workflow.trigger_type == trigger_type)
        if search:
            term = f"%{search.strip()}%"
            pred = or_(Workflow.name.ilike(term), Workflow.slug.ilike(term))
            statement = statement.where(pred)
            count_statement = count_statement.where(pred)
        items = self.db.scalars(
            statement.order_by(Workflow.created_at.desc()).offset(offset).limit(limit)
        ).unique().all()
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, workflow_id: UUID) -> Workflow | None:
        return self.db.scalar(self._base_statement().where(Workflow.id == workflow_id))

    def add(self, workflow: Workflow) -> None:
        self.db.add(workflow)
        self.db.flush()

    def delete(self, workflow: Workflow) -> None:
        self.db.delete(workflow)

    def slug_exists(self, project_id: UUID, slug: str) -> bool:
        return self.db.scalar(
            select(Workflow.id).where(Workflow.project_id == project_id, Workflow.slug == slug)
        ) is not None

    def generate_slug(self, project_id: UUID, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "workflow"
        candidate = base[:120]
        suffix = 1
        while self.slug_exists(project_id, candidate):
            suffix += 1
            candidate = f"{base[:110]}-{suffix}"[:120]
        return candidate

    def get_project(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def agent_exists_in_project(self, agent_id: UUID, project_id: UUID) -> bool:
        return self.db.scalar(
            select(Agent.id).where(Agent.id == agent_id, Agent.project_id == project_id)
        ) is not None

    def tool_exists_in_project(self, tool_id: UUID, project_id: UUID) -> bool:
        return self.db.scalar(
            select(Tool.id).where(Tool.id == tool_id, Tool.project_id == project_id)
        ) is not None

    def get_by_webhook_path(self, path: str) -> Workflow | None:
        """Find active workflow with webhook trigger matching path."""
        items, _ = self.list(
            status_filter=WorkflowStatus.active,
            trigger_type=WorkflowTriggerType.webhook,
            limit=200,
        )
        path_normalized = (path or "").strip().strip("/").lower()
        for wf in items:
            cfg = (wf.definition or {}).get("configuration") or {}
            trigger_cfg = cfg.get("trigger_config") or cfg
            webhook_cfg = trigger_cfg.get("webhook") or {}
            wp = (webhook_cfg.get("path") or wf.slug or "").strip().strip("/").lower()
            if wp and path_normalized == wp:
                return wf
        return None

    def list_scheduled(self) -> list[Workflow]:
        """List active workflows with scheduled trigger."""
        items, _ = self.list(
            status_filter=WorkflowStatus.active,
            trigger_type=WorkflowTriggerType.scheduled,
            limit=500,
        )
        return items

    def list_by_event(self, source: str, event: str) -> list[Workflow]:
        """List active workflows triggered by source.event."""
        items, _ = self.list(
            status_filter=WorkflowStatus.active,
            trigger_type=WorkflowTriggerType.event,
            limit=500,
        )
        matched = []
        for wf in items:
            cfg = (wf.definition or {}).get("configuration") or {}
            trigger_cfg = cfg.get("trigger_config") or cfg
            ev_cfg = trigger_cfg.get("event") or {}
            s = (ev_cfg.get("source") or "").strip().lower()
            e = (ev_cfg.get("event") or "").strip().lower()
            if s == source.lower() and e == event.lower():
                matched.append(wf)
        return matched

    def _base_statement(self) -> Select[tuple[Workflow]]:
        return select(Workflow).options(
            joinedload(Workflow.project),
            selectinload(Workflow.steps).joinedload(WorkflowStep.tool),
        )
