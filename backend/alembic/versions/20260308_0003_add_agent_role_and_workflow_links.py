"""add agent role and workflow links

Revision ID: 20260308_0003
Revises: 20260308_0002
Create Date: 2026-03-08 15:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260308_0003"
down_revision = "20260308_0002"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    from sqlalchemy import inspect
    insp = inspect(conn)
    cols = insp.get_columns(table)
    return any(c.get("name") == column for c in cols)


def upgrade() -> None:
    conn = op.get_bind()
    if not _column_exists(conn, "agents", "role"):
        op.add_column("agents", sa.Column("role", sa.String(length=120), server_default="software_engineer", nullable=False))
        op.execute("UPDATE agents SET role = role_title WHERE role IS NULL OR role = 'software_engineer'")
    op.create_index("ix_agents_project_role", "agents", ["project_id", "role"], unique=False, if_not_exists=True)

    op.create_table(
        "agent_workflow_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_workflow_links_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.id"],
            name="fk_agent_workflow_links_workflow_id_workflows",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_workflow_links"),
        sa.UniqueConstraint("agent_id", "workflow_id", name="uq_agent_workflow_links_agent_id_workflow_id"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_workflow_links_agent_id", "agent_workflow_links", ["agent_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_workflow_links_workflow_id", "agent_workflow_links", ["workflow_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_agent_workflow_links_workflow_id", table_name="agent_workflow_links")
    op.drop_index("ix_agent_workflow_links_agent_id", table_name="agent_workflow_links")
    op.drop_table("agent_workflow_links")

    op.drop_index("ix_agents_project_role", table_name="agents")
    op.drop_column("agents", "role")
