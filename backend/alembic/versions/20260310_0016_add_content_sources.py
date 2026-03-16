"""add content_sources table

Revision ID: 20260310_0016
Revises: 20260310_0015
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0016"
down_revision = "20260310_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE content_source_type AS ENUM ('api', 'rss');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    cs_type = postgresql.ENUM("api", "rss", name="content_source_type", create_type=False)
    op.create_table(
        "content_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", cs_type, nullable=False),
        sa.Column("api_endpoint", sa.String(length=512), nullable=False),
        sa.Column("auth", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("schema", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_content_sources_tenant_id", "content_sources", ["tenant_id"], unique=False, if_not_exists=True)
    op.create_index("ix_content_sources_type_enabled", "content_sources", ["type", "enabled"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_content_sources_type_enabled", table_name="content_sources")
    op.drop_index("ix_content_sources_tenant_id", table_name="content_sources")
    op.drop_table("content_sources")
    op.execute("DROP TYPE IF EXISTS content_source_type")
