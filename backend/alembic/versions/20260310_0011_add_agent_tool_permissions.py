"""add agent_tool_permissions table for tool slug-based permissions

Revision ID: 20260310_0011
Revises: 20260310_0010
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0011"
down_revision = "20260310_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_tool_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_slug", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "tool_slug", name="uq_agent_tool_permissions_agent_id_tool_slug"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_agent_tool_permissions_agent_id",
        "agent_tool_permissions",
        ["agent_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_agent_tool_permissions_tool_slug",
        "agent_tool_permissions",
        ["tool_slug"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_tool_permissions_tool_slug", table_name="agent_tool_permissions")
    op.drop_index("ix_agent_tool_permissions_agent_id", table_name="agent_tool_permissions")
    op.drop_table("agent_tool_permissions")
