"""add agent_instances table (Agent Instance from AgentTemplate)

Revision ID: 20260310_0021
Revises: 20260310_0020
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0021"
down_revision = "20260310_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=120), nullable=False, server_default="gpt-4"),
        sa.Column("tools_override", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["agent_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_instances_tenant_id", "agent_instances", ["tenant_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_instances_project_id", "agent_instances", ["project_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_instances_template_id", "agent_instances", ["template_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_instances_enabled", "agent_instances", ["enabled"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_agent_instances_enabled", table_name="agent_instances")
    op.drop_index("ix_agent_instances_template_id", table_name="agent_instances")
    op.drop_index("ix_agent_instances_project_id", table_name="agent_instances")
    op.drop_index("ix_agent_instances_tenant_id", table_name="agent_instances")
    op.drop_table("agent_instances")
