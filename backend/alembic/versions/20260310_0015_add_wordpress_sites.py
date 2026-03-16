"""add wordpress_sites table

Revision ID: 20260310_0015
Revises: 20260310_0014
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0015"
down_revision = "20260310_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE wordpress_site_status AS ENUM ('active', 'inactive', 'error');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    wp_status = postgresql.ENUM("active", "inactive", "error", name="wordpress_site_status", create_type=False)
    op.create_table(
        "wordpress_sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("api_url", sa.String(length=512), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("app_password", sa.String(length=255), nullable=False),
        sa.Column("status", wp_status, server_default="active", nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_wordpress_sites_tenant_id", "wordpress_sites", ["tenant_id"], unique=False, if_not_exists=True)
    op.create_index("ix_wordpress_sites_project_id", "wordpress_sites", ["project_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_wordpress_sites_project_id", table_name="wordpress_sites")
    op.drop_index("ix_wordpress_sites_tenant_id", table_name="wordpress_sites")
    op.drop_table("wordpress_sites")
    op.execute("DROP TYPE IF EXISTS wordpress_site_status")
