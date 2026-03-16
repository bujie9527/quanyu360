"""add platform_domains table

Revision ID: 20260310_0023
Revises: 20260310_0022
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0023"
down_revision = "20260310_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE platform_domain_status AS ENUM ('available', 'assigned', 'inactive');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    status_enum = postgresql.ENUM("available", "assigned", "inactive", name="platform_domain_status", create_type=False)
    op.create_table(
        "platform_domains",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("api_base_url", sa.String(length=512), nullable=False),
        sa.Column("ssl_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("status", status_enum, server_default="available", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", name="uq_platform_domains_domain"),
        if_not_exists=True,
    )
    op.create_index("ix_platform_domains_status", "platform_domains", ["status"], unique=False, if_not_exists=True)
    op.create_index("ix_platform_domains_domain", "platform_domains", ["domain"], unique=True, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_platform_domains_domain", table_name="platform_domains")
    op.drop_index("ix_platform_domains_status", table_name="platform_domains")
    op.drop_table("platform_domains")
    op.execute("DROP TYPE IF EXISTS platform_domain_status")
