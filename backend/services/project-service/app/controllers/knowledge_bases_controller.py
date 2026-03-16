"""Knowledge base HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status

from app.dependencies import get_db_session
from app.dependencies import get_tenant_context_dep
from app.schemas.knowledge_base_schemas import DocumentResponse
from app.schemas.knowledge_base_schemas import DocumentUploadRequest
from app.schemas.knowledge_base_schemas import KnowledgeBaseCreateRequest
from app.schemas.knowledge_base_schemas import KnowledgeBaseResponse
from app.schemas.knowledge_base_schemas import SearchRequest
from app.schemas.knowledge_base_schemas import SearchResponse
from app.schemas.knowledge_base_schemas import SearchResultItem
from app.services.knowledge_base_service import KnowledgeBaseService
from common.app.auth import TenantContext
from sqlalchemy.orm import Session

router = APIRouter(prefix="/projects", tags=["knowledge-bases"])


def _get_kb_service(db: Session = Depends(get_db_session)) -> KnowledgeBaseService:
    return KnowledgeBaseService(db)


@router.get("/{project_id}/knowledge-bases", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases(
    project_id: UUID,
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> list[KnowledgeBaseResponse]:
    """List knowledge bases for a project."""
    kbs = service.list_knowledge_bases(project_id)
    return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]


@router.post("/{project_id}/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    project_id: UUID,
    payload: KnowledgeBaseCreateRequest,
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> KnowledgeBaseResponse:
    """Create a knowledge base."""
    kb = service.create_knowledge_base(
        project_id=project_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        embedding_model=payload.embedding_model,
    )
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{project_id}/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    project_id: UUID,
    kb_id: UUID,
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> KnowledgeBaseResponse:
    """Get a knowledge base with documents."""
    kb = service.get_knowledge_base(kb_id, project_id=project_id)
    return KnowledgeBaseResponse.model_validate(kb)


@router.post("/{project_id}/knowledge-bases/{kb_id}/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    kb_id: UUID,
    file: UploadFile | None = File(None),
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> DocumentResponse:
    """Upload a document (file or JSON body). Supports text/plain, application/json."""
    service.get_knowledge_base(kb_id, project_id=project_id)
    if file:
        content = (await file.read()).decode("utf-8", errors="replace")
        filename = file.filename or "document.txt"
        mime_type = file.content_type or "text/plain"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided. Use multipart form with 'file'.")
    doc = service.upload_document(knowledge_base_id=kb_id, filename=filename, content=content, mime_type=mime_type)
    return DocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status.value,
        last_error=doc.last_error,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post("/{project_id}/knowledge-bases/{kb_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def add_document_json(
    project_id: UUID,
    kb_id: UUID,
    payload: DocumentUploadRequest,
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> DocumentResponse:
    """Add document from JSON body (content + filename)."""
    service.get_knowledge_base(kb_id, project_id=project_id)
    doc = service.upload_document(
        knowledge_base_id=kb_id,
        filename=payload.filename,
        content=payload.content,
        mime_type=payload.mime_type,
    )
    return DocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status.value,
        last_error=doc.last_error,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post("/{project_id}/knowledge-bases/{kb_id}/search", response_model=SearchResponse)
def search_documents(
    project_id: UUID,
    kb_id: UUID,
    payload: SearchRequest,
    service: KnowledgeBaseService = Depends(_get_kb_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> SearchResponse:
    """Semantic search over knowledge base documents."""
    service.get_knowledge_base(kb_id, project_id=project_id)
    raw = service.search(knowledge_base_id=kb_id, query=payload.query, limit=payload.limit)
    results = [
        SearchResultItem(
            id=r.get("id", ""),
            score=r.get("score", 0.0),
            content=(r.get("payload") or {}).get("content", ""),
            document_id=(r.get("payload") or {}).get("document_id"),
            chunk_index=(r.get("payload") or {}).get("chunk_index"),
        )
        for r in raw
    ]
    return SearchResponse(results=results)
