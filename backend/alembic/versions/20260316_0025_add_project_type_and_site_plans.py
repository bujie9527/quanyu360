"""add project type and site plan tables

Revision ID: 20260316_0025
Revises: 20260310_0024
Create Date: 2026-03-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260316_0025"
down_revision = "20260310_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    project_type_enum = sa.Enum("general", "matrix_site", name="project_type")
    site_plan_status_enum = sa.Enum("draft", "approved", "executing", name="site_plan_status")
    site_plan_item_status_enum = sa.Enum("planned", "building", "active", name="site_plan_item_status")

    bind = op.get_bind()
    project_type_enum.create(bind, checkfirst=True)
    site_plan_status_enum.create(bind, checkfirst=True)
    site_plan_item_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "projects",
        sa.Column("project_type", project_type_enum, nullable=False, server_default="general"),
    )
    op.add_column(
        "projects",
        sa.Column("matrix_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "site_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", site_plan_status_enum, nullable=False, server_default="draft"),
        sa.Column("agent_input", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("agent_output", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_plans_project_id", "site_plans", ["project_id"], unique=False)
    op.create_index("ix_site_plans_status", "site_plans", ["status"], unique=False)

    op.create_table(
        "site_plan_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("site_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_name", sa.String(length=255), nullable=False),
        sa.Column("site_theme", sa.String(length=255), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("content_direction", sa.Text(), nullable=False),
        sa.Column("seo_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("site_structure", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("wordpress_site_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", site_plan_item_status_enum, nullable=False, server_default="planned"),
        sa.ForeignKeyConstraint(["site_plan_id"], ["site_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wordpress_site_id"], ["wordpress_sites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_plan_items_site_plan_id", "site_plan_items", ["site_plan_id"], unique=False)
    op.create_index("ix_site_plan_items_status", "site_plan_items", ["status"], unique=False)
    op.create_index("ix_site_plan_items_wordpress_site_id", "site_plan_items", ["wordpress_site_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_site_plan_items_wordpress_site_id", table_name="site_plan_items")
    op.drop_index("ix_site_plan_items_status", table_name="site_plan_items")
    op.drop_index("ix_site_plan_items_site_plan_id", table_name="site_plan_items")
    op.drop_table("site_plan_items")

    op.drop_index("ix_site_plans_status", table_name="site_plans")
    op.drop_index("ix_site_plans_project_id", table_name="site_plans")
    op.drop_table("site_plans")

    op.drop_column("projects", "matrix_config")
    op.drop_column("projects", "project_type")

    bind = op.get_bind()
    sa.Enum(name="site_plan_item_status").drop(bind, checkfirst=True)
    sa.Enum(name="site_plan_status").drop(bind, checkfirst=True)
    sa.Enum(name="project_type").drop(bind, checkfirst=True)
