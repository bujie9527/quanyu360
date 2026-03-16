"""TaskRun and StepRun data access."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload

from common.app.models import Project
from common.app.models import StepRun
from common.app.models import TaskRun
from common.app.models import Workflow


class TaskRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        workflow_id: UUID,
        execution_id: str,
        task_template_id: UUID | None = None,
    ) -> TaskRun:
        tr = TaskRun(
            workflow_id=workflow_id,
            execution_id=execution_id,
            task_template_id=task_template_id,
            status="running",
        )
        self.db.add(tr)
        self.db.flush()
        return tr

    def get(self, task_run_id: UUID) -> TaskRun | None:
        return self.db.get(TaskRun, task_run_id)

    def update_status(
        self,
        task_run_id: UUID,
        status: str,
        end_time: datetime | None = None,
    ) -> TaskRun | None:
        tr = self.db.get(TaskRun, task_run_id)
        if tr is None:
            return None
        tr.status = status
        if end_time is not None:
            tr.end_time = end_time
        self.db.flush()
        return tr

    def list(
        self,
        task_template_id: UUID | None = None,
        workflow_id: UUID | None = None,
        project_id: UUID | None = None,
        tenant_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskRun], int]:
        stmt = (
            select(TaskRun)
            .join(Workflow, TaskRun.workflow_id == Workflow.id)
            .join(Project, Workflow.project_id == Project.id)
        )
        count_stmt = (
            select(func.count())
            .select_from(TaskRun)
            .join(Workflow, TaskRun.workflow_id == Workflow.id)
            .join(Project, Workflow.project_id == Project.id)
        )
        if task_template_id is not None:
            stmt = stmt.where(TaskRun.task_template_id == task_template_id)
            count_stmt = count_stmt.where(TaskRun.task_template_id == task_template_id)
        if workflow_id is not None:
            stmt = stmt.where(TaskRun.workflow_id == workflow_id)
            count_stmt = count_stmt.where(TaskRun.workflow_id == workflow_id)
        if project_id is not None:
            stmt = stmt.where(Workflow.project_id == project_id)
            count_stmt = count_stmt.where(Workflow.project_id == project_id)
        if tenant_id is not None:
            stmt = stmt.where(Project.tenant_id == tenant_id)
            count_stmt = count_stmt.where(Project.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(TaskRun.status == status)
            count_stmt = count_stmt.where(TaskRun.status == status)
        total = int(self.db.scalar(count_stmt) or 0)
        items = list(
            self.db.scalars(stmt.order_by(TaskRun.start_time.desc()).offset(offset).limit(limit))
        )
        return items, total

    def get_by_tenant(self, task_run_id: UUID, tenant_id: UUID) -> TaskRun | None:
        """Get TaskRun only if it belongs to the tenant (via workflow.project.tenant_id)."""
        stmt = (
            select(TaskRun)
            .join(Workflow, TaskRun.workflow_id == Workflow.id)
            .join(Project, Workflow.project_id == Project.id)
            .where(TaskRun.id == task_run_id, Project.tenant_id == tenant_id)
            .options(joinedload(TaskRun.step_runs))
        )
        result = self.db.execute(stmt)
        return result.unique().scalars().first()

    def append_step(
        self,
        task_run_id: UUID,
        step_name: str,
        status: str,
        duration: float,
        output_json: dict,
    ) -> StepRun | None:
        tr = self.db.get(TaskRun, task_run_id)
        if tr is None:
            return None
        sr = StepRun(
            task_run_id=task_run_id,
            step_name=step_name,
            status=status,
            duration=duration,
            output_json=output_json or {},
        )
        self.db.add(sr)
        self.db.flush()
        return sr
