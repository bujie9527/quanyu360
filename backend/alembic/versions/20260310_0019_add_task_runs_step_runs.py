"""add task_runs and step_runs tables (Execution Log)

Revision ID: 20260310_0019
Revises: 20260310_0018
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0019"
down_revision = "20260310_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("task_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("start_time", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_template_id"], ["task_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_task_runs_task_template_id", "task_runs", ["task_template_id"], unique=False, if_not_exists=True)
    op.create_index("ix_task_runs_workflow_id", "task_runs", ["workflow_id"], unique=False, if_not_exists=True)
    op.create_index("ix_task_runs_status", "task_runs", ["status"], unique=False, if_not_exists=True)

    op.create_table(
        "step_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("task_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False, server_default="0"),
        sa.Column("output_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_step_runs_task_run_id", "step_runs", ["task_run_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_step_runs_task_run_id", table_name="step_runs")
    op.drop_table("step_runs")
    op.drop_index("ix_task_runs_status", table_name="task_runs")
    op.drop_index("ix_task_runs_workflow_id", table_name="task_runs")
    op.drop_index("ix_task_runs_task_template_id", table_name="task_runs")
    op.drop_table("task_runs")
