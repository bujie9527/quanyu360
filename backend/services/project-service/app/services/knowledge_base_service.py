"""Knowledge base business logic: upload, embed, search."""
from __future__ import annotations

import hashlib
import uuid
from uuid import UUID

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.repositories import KnowledgeBaseRepository
from app.repositories import ProjectRepository
from app.repositories.knowledge_base_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantKnowledgeStore
from common.app.models import Document
from common.app.models import DocumentEmbedding
from common.app.models import DocumentStatus
from common.app.models import KnowledgeBase

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Try to break at paragraph or sentence
            for sep in ("\n\n", "\n", ". ", " "):
                last = text.rfind(sep, start, end + 1)
                if last >= start:
                    end = last + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end < len(text) else len(text)
    return chunks


class KnowledgeBaseService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository | None = None,
        kb_repo: KnowledgeBaseRepository | None = None,
        doc_repo: DocumentRepository | None = None,
    ):
        self.db = db
        self.project_repo = project_repo or ProjectRepository(db)
        self.kb_repo = kb_repo or KnowledgeBaseRepository(db)
        self.doc_repo = doc_repo or DocumentRepository(db)
        self.embedding_svc = EmbeddingService()
        self.qdrant = QdrantKnowledgeStore()

    def list_knowledge_bases(self, project_id: UUID) -> list[KnowledgeBase]:
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return self.kb_repo.get_by_project(project_id)

    def create_knowledge_base(
        self,
        project_id: UUID,
        name: str,
        slug: str,
        description: str | None = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> KnowledgeBase:
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        existing = self.kb_repo.get_by_project_and_slug(project_id, slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Knowledge base '{slug}' already exists.")
        kb = KnowledgeBase(
            project_id=project_id,
            name=name,
            slug=slug,
            description=description,
            embedding_model=embedding_model,
        )
        self.kb_repo.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        self.qdrant.ensure_collection(str(kb.id))
        return kb

    def get_knowledge_base(self, kb_id: UUID, project_id: UUID | None = None) -> KnowledgeBase:
        kb = self.kb_repo.get_with_documents(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
        if project_id and kb.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
        return kb

    def upload_document(
        self,
        knowledge_base_id: UUID,
        filename: str,
        content: str,
        mime_type: str | None = None,
    ) -> Document:
        kb = self.get_knowledge_base(knowledge_base_id)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        doc = Document(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            mime_type=mime_type or "text/plain",
            content_hash=content_hash,
            status=DocumentStatus.processing,
        )
        self.doc_repo.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        try:
            chunks = _chunk_text(content)
            if not chunks:
                doc.status = DocumentStatus.embedded
                doc.last_error = None
                self.db.commit()
                self.db.refresh(doc)
                return doc

            if not self.embedding_svc._get_client():
                doc.status = DocumentStatus.failed
                doc.last_error = "OpenAI API not configured"
                self.db.commit()
                self.db.refresh(doc)
                return doc

            vectors = self.embedding_svc.embed(chunks, model=kb.embedding_model)
            if len(vectors) != len(chunks):
                doc.status = DocumentStatus.failed
                doc.last_error = "Embedding failed"
                self.db.commit()
                self.db.refresh(doc)
                return doc

            self.qdrant.ensure_collection(str(knowledge_base_id))
            point_ids = [str(uuid.uuid4()) for _ in chunks]
            payloads = [
                {"document_id": str(doc.id), "chunk_index": i, "content": c}
                for i, c in enumerate(chunks)
            ]
            ok = self.qdrant.upsert(str(knowledge_base_id), point_ids, vectors, payloads)
            if not ok:
                doc.status = DocumentStatus.failed
                doc.last_error = "Qdrant upsert failed"
                self.db.commit()
                self.db.refresh(doc)
                return doc

            for i, (c, pid) in enumerate(zip(chunks, point_ids)):
                emb = DocumentEmbedding(
                    document_id=doc.id,
                    chunk_index=i,
                    content=c,
                    qdrant_point_id=pid,
                )
                self.doc_repo.add_embedding(emb)
            doc.status = DocumentStatus.embedded
            doc.last_error = None
            self.db.commit()
            self.db.refresh(doc)
            return doc
        except Exception as e:
            doc.status = DocumentStatus.failed
            doc.last_error = str(e)
            self.db.commit()
            self.db.refresh(doc)
            return doc

    def search(
        self,
        knowledge_base_id: UUID,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        kb = self.get_knowledge_base(knowledge_base_id)
        if not self.embedding_svc._get_client():
            return []
        vectors = self.embedding_svc.embed([query], model=kb.embedding_model)
        if not vectors:
            return []
        results = self.qdrant.search(str(knowledge_base_id), vectors[0], limit=limit)
        return results
