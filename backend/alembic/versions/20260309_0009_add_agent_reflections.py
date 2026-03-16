"""add agent_reflections table

Revision ID: 20260309_0009
Revises: 20260309_0008
Create Date: 2026-03-09

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260309_0009"
down_revision = "20260309_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_reflections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("issues", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("improvement", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_reflections_task_id", "agent_reflections", ["task_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_reflections_agent_id", "agent_reflections", ["agent_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_agent_reflections_agent_id", table_name="agent_reflections")
    op.drop_index("ix_agent_reflections_task_id", table_name="agent_reflections")
    op.drop_table("agent_reflections")
