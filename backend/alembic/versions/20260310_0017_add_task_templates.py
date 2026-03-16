"""add task_templates table

Revision ID: 20260310_0017
Revises: 20260310_0016
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0017"
down_revision = "20260310_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parameters_schema", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_task_templates_project_id", "task_templates", ["project_id"], unique=False, if_not_exists=True)
    op.create_index("ix_task_templates_workflow_id", "task_templates", ["workflow_id"], unique=False, if_not_exists=True)
    op.create_index("ix_task_templates_enabled", "task_templates", ["enabled"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_task_templates_enabled", table_name="task_templates")
    op.drop_index("ix_task_templates_workflow_id", table_name="task_templates")
    op.drop_index("ix_task_templates_project_id", table_name="task_templates")
    op.drop_table("task_templates")
