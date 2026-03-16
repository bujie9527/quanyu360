"""Knowledge base and document data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from common.app.models import Document
from common.app.models import DocumentEmbedding
from common.app.models import DocumentStatus
from common.app.models import KnowledgeBase
from common.app.models import Project


class KnowledgeBaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_project(self, project_id: UUID) -> list[KnowledgeBase]:
        stmt = select(KnowledgeBase).where(KnowledgeBase.project_id == project_id)
        return list(self.db.scalars(stmt).all())

    def get(self, kb_id: UUID) -> KnowledgeBase | None:
        return self.db.get(KnowledgeBase, kb_id)

    def get_with_documents(self, kb_id: UUID) -> KnowledgeBase | None:
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.id == kb_id)
            .options(selectinload(KnowledgeBase.documents))
        )
        return self.db.scalar(stmt)

    def get_by_project_and_slug(self, project_id: UUID, slug: str) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.project_id == project_id,
            KnowledgeBase.slug == slug,
        )
        return self.db.scalar(stmt)

    def add(self, kb: KnowledgeBase) -> None:
        self.db.add(kb)
        self.db.flush()


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, doc_id: UUID) -> Document | None:
        return self.db.get(Document, doc_id)

    def get_with_embeddings(self, doc_id: UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == doc_id)
            .options(selectinload(Document.embeddings))
        )
        return self.db.scalar(stmt)

    def add(self, doc: Document) -> None:
        self.db.add(doc)
        self.db.flush()

    def add_embedding(self, emb: DocumentEmbedding) -> None:
        self.db.add(emb)
        self.db.flush()
