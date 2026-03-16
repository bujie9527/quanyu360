"""UsageTracker: persist usage events to usage_logs per tenant."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.app.models import UsageLog
from common.app.models import UsageType


class UsageSummary:
    """Aggregated usage per tenant."""

    def __init__(
        self,
        tenant_id: UUID,
        llm_tokens_total: int,
        llm_prompt_tokens: int,
        llm_completion_tokens: int,
        workflow_runs: int,
        tool_executions: int,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> None:
        self.tenant_id = tenant_id
        self.llm_tokens_total = llm_tokens_total
        self.llm_prompt_tokens = llm_prompt_tokens
        self.llm_completion_tokens = llm_completion_tokens
        self.workflow_runs = workflow_runs
        self.tool_executions = tool_executions
        self.from_at = from_at
        self.to_at = to_at


class UsageTracker:
    """Tracks usage (LLM tokens, workflow runs, tool executions) per tenant."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def track(
        self,
        *,
        tenant_id: str | UUID,
        usage_type: str,
        project_id: str | UUID | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        quantity: int = 1,
        metadata: dict | None = None,
    ) -> UsageLog | None:
        """Persist a usage log entry."""
        try:
            ut = UsageType(usage_type)
        except ValueError:
            return None
        tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        pid = UUID(str(project_id)) if project_id else None
        entry = UsageLog(
            tenant_id=tid,
            usage_type=ut,
            project_id=pid,
            prompt_tokens=max(0, prompt_tokens),
            completion_tokens=max(0, completion_tokens),
            quantity=max(0, quantity),
            metadata_json=metadata or {},
        )
        try:
            self.db.add(entry)
            self.db.flush()
            return entry
        except IntegrityError:
            self.db.rollback()
            return None

    def summary(
        self,
        tenant_id: str | UUID,
        from_at: datetime | None = None,
        to_at: datetime | None = None,
    ) -> UsageSummary:
        """Aggregate usage by tenant and optional date range."""
        tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        stmt = select(UsageLog).where(UsageLog.tenant_id == tid)
        if from_at:
            stmt = stmt.where(UsageLog.created_at >= from_at)
        if to_at:
            stmt = stmt.where(UsageLog.created_at <= to_at)
        rows = self.db.execute(stmt).scalars().all()

        llm_prompt = 0
        llm_completion = 0
        workflow_runs = 0
        tool_executions = 0

        for row in rows:
            if row.usage_type == UsageType.llm_tokens:
                llm_prompt += row.prompt_tokens
                llm_completion += row.completion_tokens
            elif row.usage_type == UsageType.workflow_run:
                workflow_runs += row.quantity
            elif row.usage_type == UsageType.tool_execution:
                tool_executions += row.quantity

        return UsageSummary(
            tenant_id=tid,
            llm_tokens_total=llm_prompt + llm_completion,
            llm_prompt_tokens=llm_prompt,
            llm_completion_tokens=llm_completion,
            workflow_runs=workflow_runs,
            tool_executions=tool_executions,
            from_at=from_at,
            to_at=to_at,
        )

    def list_logs(
        self,
        tenant_id: str | UUID | None = None,
        from_at: datetime | None = None,
        to_at: datetime | None = None,
        usage_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UsageLog], int]:
        """List usage logs with optional filters. Returns (items, total)."""
        stmt = select(UsageLog).order_by(UsageLog.created_at.desc())
        count_stmt = select(func.count(UsageLog.id))
        if tenant_id is not None:
            tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
            stmt = stmt.where(UsageLog.tenant_id == tid)
            count_stmt = count_stmt.where(UsageLog.tenant_id == tid)
        if from_at:
            stmt = stmt.where(UsageLog.created_at >= from_at)
            count_stmt = count_stmt.where(UsageLog.created_at >= from_at)
        if to_at:
            stmt = stmt.where(UsageLog.created_at <= to_at)
            count_stmt = count_stmt.where(UsageLog.created_at <= to_at)
        if usage_type:
            try:
                ut = UsageType(usage_type)
                stmt = stmt.where(UsageLog.usage_type == ut)
                count_stmt = count_stmt.where(UsageLog.usage_type == ut)
            except ValueError:
                pass
        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.offset(offset).limit(limit)).all())
        return items, total
