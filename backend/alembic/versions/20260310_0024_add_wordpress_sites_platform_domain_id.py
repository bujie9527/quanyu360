"""add platform_domain_id to wordpress_sites

Revision ID: 20260310_0024
Revises: 20260310_0023
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0024"
down_revision = "20260310_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "wordpress_sites",
        sa.Column("platform_domain_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_wordpress_sites_platform_domain_id",
        "wordpress_sites",
        "platform_domains",
        ["platform_domain_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_wordpress_sites_platform_domain_id",
        "wordpress_sites",
        ["platform_domain_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_wordpress_sites_platform_domain_id", table_name="wordpress_sites")
    op.drop_constraint("fk_wordpress_sites_platform_domain_id", "wordpress_sites", type_="foreignkey")
    op.drop_column("wordpress_sites", "platform_domain_id")
