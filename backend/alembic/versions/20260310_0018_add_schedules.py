"""add schedules table

Revision ID: 20260310_0018
Revises: 20260310_0017
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0018"
down_revision = "20260310_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("task_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cron", sa.String(length=60), nullable=False),
        sa.Column("target_sites", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["task_template_id"], ["task_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_schedules_task_template_id", "schedules", ["task_template_id"], unique=False, if_not_exists=True)
    op.create_index("ix_schedules_enabled", "schedules", ["enabled"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_schedules_enabled", table_name="schedules")
    op.drop_index("ix_schedules_task_template_id", table_name="schedules")
    op.drop_table("schedules")
