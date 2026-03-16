"""add assets table

Revision ID: 20260309_0006
Revises: 20260308_0005
Create Date: 2026-03-09

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260309_0006"
down_revision = "20260308_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE asset_kind AS ENUM ('file', 'document', 'image');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    asset_kind = postgresql.ENUM("file", "document", "image", name="asset_kind", create_type=False)
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("kind", asset_kind, nullable=False, server_default="file"),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_assets_tenant_project", "assets", ["tenant_id", "project_id"], if_not_exists=True)
    op.create_index("ix_assets_project_kind", "assets", ["project_id", "kind"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_assets_project_kind", table_name="assets")
    op.drop_index("ix_assets_tenant_project", table_name="assets")
    op.drop_table("assets")
    op.execute("DROP TYPE asset_kind")
