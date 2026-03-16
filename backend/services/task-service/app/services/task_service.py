"""Task business logic."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.config import settings
from app.queue import enqueue_task
from app.repositories import TaskRepository
from app.schemas.task_schemas import AnalyticsPointResponse
from app.schemas.task_schemas import TaskAnalyticsSummaryResponse
from app.schemas.task_schemas import TaskCreateRequest
from common.app.models import AgentReflection
from common.app.models import Task
from common.app.models import TaskPriority
from common.app.models import TaskStatus
from common.app.observability.prometheus import calculate_quantile


class TaskService:
    """Orchestrates task business logic."""

    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def list_tasks(
        self,
        project_id: UUID | None = None,
        agent_id: UUID | None = None,
        workflow_id: UUID | None = None,
        status_filter: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        return self.repo.list(
            project_id=project_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status_filter=status_filter,
            priority=priority,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_task(self, task_id: UUID) -> Task:
        task = self.repo.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task

    def create_task(self, payload: TaskCreateRequest) -> Task:
        project = self.repo.get_project(payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if settings.admin_service_url:
            from common.app.quota_client import check_quota
            allowed, err = check_quota(settings.admin_service_url, tenant_id=str(project.tenant_id), resource="tasks_per_month")
            if not allowed:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=err or "Tasks quota exceeded for this month.")
        agent = (
            self.repo.get_agent_in_project(payload.agent_id, project.id)
            if payload.agent_id
            else None
        )
        team = (
            self.repo.get_team_in_project(payload.team_id, project.id)
            if payload.team_id
            else None
        )
        if payload.team_id and team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent team not found.")
        workflow = (
            self.repo.get_workflow_in_project(payload.workflow_id, project.id)
            if payload.workflow_id
            else None
        )
        created_by = (
            self.repo.get_user_in_tenant(payload.created_by_user_id, project.tenant_id)
            if payload.created_by_user_id
            else None
        )
        if payload.team_id and payload.agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task cannot have both agent_id and team_id.",
            )
        task = Task(
            project_id=project.id,
            agent=agent,
            team=team,
            workflow=workflow,
            created_by=created_by,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=TaskStatus.pending,
            attempt_count=0,
            max_attempts=payload.max_attempts or settings.task_default_max_attempts,
            due_at=payload.due_at,
            input_payload=payload.input_payload,
            output_payload={},
        )
        self.repo.add(task)
        self.repo.db.commit()
        return self.get_task(task.id)

    def run_task(self, task_id: UUID) -> Task:
        task = self.get_task(task_id)
        if task.status == TaskStatus.completed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed tasks cannot be enqueued again.")
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is already running.")
        if task.status == TaskStatus.cancelled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled tasks cannot be enqueued.")
        if task.status == TaskStatus.failed:
            task.attempt_count = 0
        task.status = TaskStatus.pending
        task.last_error = None
        task.started_at = None
        task.completed_at = None
        self.repo.db.commit()
        enqueue_task(task.id)
        return self.get_task(task.id)

    def cancel_task(self, task_id: UUID) -> Task:
        task = self.get_task(task_id)
        if task.status == TaskStatus.completed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed tasks cannot be cancelled.")
        task.status = TaskStatus.cancelled
        task.last_error = "Task cancelled by operator."
        task.completed_at = datetime.now(timezone.utc)
        self.repo.db.commit()
        return self.get_task(task.id)

    def mark_task_running(self, task_id: UUID) -> Task:
        task = self.get_task(task_id)
        if task.status == TaskStatus.cancelled:
            return task
        task.status = TaskStatus.running
        task.attempt_count += 1
        task.started_at = datetime.now(timezone.utc)
        task.last_error = None
        self.repo.db.commit()
        return self.get_task(task.id)

    def mark_task_completed(self, task_id: UUID, output_payload: dict[str, object]) -> Task:
        task = self.get_task(task_id)
        task.status = TaskStatus.completed
        task.output_payload = output_payload
        task.completed_at = datetime.now(timezone.utc)
        task.last_error = None
        reflection_data = output_payload.get("reflection")
        if isinstance(reflection_data, dict):
            success = bool(reflection_data.get("success", True))
            issues = reflection_data.get("issues", [])
            if not isinstance(issues, list):
                issues = [str(issues)] if issues else []
            issues = [str(i)[:500] for i in issues[:20]]
            improvement = str(reflection_data.get("improvement", "") or "")[:2000]
            reflection = AgentReflection(
                task_id=task.id,
                agent_id=task.agent_id,
                success=success,
                issues=issues,
                improvement=improvement,
            )
            self.repo.db.add(reflection)
        self.repo.db.commit()
        return self.get_task(task.id)

    def mark_task_failed(self, task_id: UUID, error_message: str, output_payload: dict | None = None) -> Task:
        task = self.get_task(task_id)
        task.last_error = error_message
        if output_payload is not None:
            task.output_payload = output_payload
        if task.status == TaskStatus.cancelled:
            self.repo.db.commit()
            return self.get_task(task.id)
        if task.attempt_count < task.max_attempts:
            task.status = TaskStatus.pending
            self.repo.db.commit()
            enqueue_task(task.id)
        else:
            task.status = TaskStatus.failed
            task.completed_at = datetime.now(timezone.utc)
            self.repo.db.commit()
        return self.get_task(task.id)

    def get_task_analytics_summary(self) -> TaskAnalyticsSummaryResponse:
        tasks = self.repo.get_all_ordered_by_created()
        status_totals = {s.value: 0 for s in TaskStatus}
        recent_volume = self._build_recent_task_volume(tasks)
        execution_time_breakdown = self._build_execution_time_breakdown(tasks)
        tasks_executed = 0
        completed_tasks = 0
        failed_tasks = 0
        pending_tasks = 0
        running_tasks = 0
        durations: list[float] = []
        for task in tasks:
            status_totals[task.status.value] = status_totals.get(task.status.value, 0) + 1
            tasks_executed += task.attempt_count
            if task.status == TaskStatus.completed:
                completed_tasks += 1
            elif task.status == TaskStatus.failed:
                failed_tasks += 1
            elif task.status == TaskStatus.pending:
                pending_tasks += 1
            elif task.status == TaskStatus.running:
                running_tasks += 1
            if task.started_at and task.completed_at and task.completed_at >= task.started_at:
                durations.append((task.completed_at - task.started_at).total_seconds())
        finalized = completed_tasks + failed_tasks
        success_rate = completed_tasks / finalized if finalized else 0.0
        average_duration = sum(durations) / len(durations) if durations else 0.0
        p95_duration = calculate_quantile(durations, 0.95)
        status_breakdown = [
            AnalyticsPointResponse(label=name.replace("_", " ").title(), value=float(count))
            for name, count in sorted(status_totals.items())
        ]
        return TaskAnalyticsSummaryResponse(
            tasks_executed=tasks_executed,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            pending_tasks=pending_tasks,
            running_tasks=running_tasks,
            agent_success_rate=round(success_rate, 6),
            average_execution_time_seconds=round(average_duration, 6),
            p95_execution_time_seconds=round(p95_duration, 6),
            status_breakdown=status_breakdown,
            recent_task_volume=recent_volume,
            execution_time_breakdown=execution_time_breakdown,
        )

    def _build_recent_task_volume(self, tasks: list[Task]) -> list[AnalyticsPointResponse]:
        today = datetime.now(timezone.utc).date()
        recent_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        volume_by_day = {day: 0 for day in recent_days}
        for task in tasks:
            created_day = task.created_at.astimezone(timezone.utc).date()
            if created_day in volume_by_day:
                volume_by_day[created_day] += 1
        return [
            AnalyticsPointResponse(label=day.strftime("%b %d"), value=float(volume_by_day[day]))
            for day in recent_days
        ]

    def _build_execution_time_breakdown(self, tasks: list[Task]) -> list[AnalyticsPointResponse]:
        completed = [
            t for t in tasks
            if t.started_at is not None and t.completed_at is not None and t.completed_at >= t.started_at
        ]
        completed.sort(key=lambda t: t.completed_at or t.created_at, reverse=True)
        return [
            AnalyticsPointResponse(
                label=(t.title[:18] + "...") if len(t.title) > 18 else t.title,
                value=round((t.completed_at - t.started_at).total_seconds(), 6),
            )
            for t in completed[:6]
        ]
