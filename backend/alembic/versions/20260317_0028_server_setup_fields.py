"""Add setup_status, setup_log to servers; make mysql fields nullable; add pending_setup status.

Revision ID: 20260317_0028
Revises: 20260317_0027
Create Date: 2026-03-17

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260317_0028"
down_revision = "20260317_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pending_setup to server_status enum
    op.execute("ALTER TYPE server_status ADD VALUE IF NOT EXISTS 'pending_setup'")

    # Create server_setup_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE server_setup_status AS ENUM ('pending', 'running', 'completed', 'failed');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Add setup_status column
    op.add_column(
        "servers",
        sa.Column(
            "setup_status",
            sa.Enum("pending", "running", "completed", "failed", name="server_setup_status"),
            nullable=False,
            server_default="pending",
        ),
    )

    # Add setup_log column
    op.add_column(
        "servers",
        sa.Column("setup_log", sa.Text(), nullable=True),
    )

    # Make mysql_admin_user nullable
    op.alter_column("servers", "mysql_admin_user", nullable=True)

    # Make mysql_admin_password nullable
    op.alter_column("servers", "mysql_admin_password", nullable=True)

    # Update web_root default
    op.alter_column(
        "servers",
        "web_root",
        server_default="/var/www",
        existing_nullable=False,
    )

    # Add index on setup_status
    op.create_index("ix_servers_setup_status", "servers", ["setup_status"])


def downgrade() -> None:
    op.drop_index("ix_servers_setup_status", table_name="servers")
    op.drop_column("servers", "setup_log")
    op.drop_column("servers", "setup_status")
    op.alter_column("servers", "mysql_admin_user", nullable=False)
    op.alter_column("servers", "mysql_admin_password", nullable=False)
