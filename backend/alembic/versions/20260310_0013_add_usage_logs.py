"""add usage_logs table for usage tracking per tenant

Revision ID: 20260310_0013
Revises: 20260310_0012
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0013"
down_revision = "20260310_0012"
branch_labels = None
depends_on = None

def _create_enum_if_not_exists(name: str, values: list[str]) -> str:
    vals = ", ".join(f"'{v}'" for v in values)
    return f"""
    DO $$ BEGIN
        CREATE TYPE {name} AS ENUM ({vals});
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """


usage_type = postgresql.ENUM("llm_tokens", "workflow_run", "tool_execution", name="usage_type", create_type=False)


def upgrade() -> None:
    op.execute(_create_enum_if_not_exists("usage_type", ["llm_tokens", "workflow_run", "tool_execution"]))

    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_type", usage_type, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_usage_logs_tenant_type", "usage_logs", ["tenant_id", "usage_type"], unique=False, if_not_exists=True)
    op.create_index("ix_usage_logs_tenant_created", "usage_logs", ["tenant_id", "created_at"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_usage_logs_tenant_created", table_name="usage_logs")
    op.drop_index("ix_usage_logs_tenant_type", table_name="usage_logs")
    op.drop_table("usage_logs")
    usage_type.drop(op.get_bind(), checkfirst=True)
