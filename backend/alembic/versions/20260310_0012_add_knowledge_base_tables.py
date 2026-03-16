"""add knowledge bases, documents, document_embeddings tables

Revision ID: 20260310_0012
Revises: 20260310_0011
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0012"
down_revision = "20260310_0011"
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


document_status = postgresql.ENUM("pending", "processing", "embedded", "failed", name="document_status", create_type=False)


def upgrade() -> None:
    op.execute(_create_enum_if_not_exists("document_status", ["pending", "processing", "embedded", "failed"]))

    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.String(length=80), server_default="text-embedding-3-small", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "slug", name="uq_knowledge_bases_project_id_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_knowledge_bases_project", "knowledge_bases", ["project_id"], unique=False, if_not_exists=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("status", document_status, server_default="pending", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_documents_knowledge_base_status", "documents", ["knowledge_base_id", "status"], unique=False, if_not_exists=True)

    op.create_table(
        "document_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("qdrant_point_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_document_embeddings_document", "document_embeddings", ["document_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_document_embeddings_document", table_name="document_embeddings")
    op.drop_table("document_embeddings")
    op.drop_index("ix_documents_knowledge_base_status", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_knowledge_bases_project", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")
    document_status.drop(op.get_bind(), checkfirst=True)
