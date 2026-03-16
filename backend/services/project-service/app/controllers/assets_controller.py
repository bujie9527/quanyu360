"""Asset HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile

from app.dependencies import get_asset_service
from app.dependencies import get_tenant_context_required
from app.schemas.asset_schemas import AssetUploadResponse
from app.services import AssetService
from common.app.auth import TenantContext
from common.app.storage import get_storage

router = APIRouter(prefix="/projects", tags=["assets"])


@router.post("/{project_id}/assets/upload", response_model=AssetUploadResponse, tags=["assets"])
async def upload_asset(
    project_id: UUID,
    file: UploadFile = File(...),
    asset_service: AssetService = Depends(get_asset_service),
    ctx: TenantContext = Depends(get_tenant_context_required),
) -> AssetUploadResponse:
    """Upload an asset to project. Requires tenant context."""
    storage = get_storage()
    key = storage.generate_key(str(ctx.tenant_id), str(project_id), file.filename or "unnamed")
    data = await file.read()
    storage.put(key, data, content_type=file.content_type)

    asset = asset_service.upload_asset(
        project_id=project_id,
        tenant_id=ctx.tenant_id,
        filename=file.filename or "unnamed",
        storage_key=key,
        content_type=file.content_type,
        size_bytes=len(data),
    )
    return AssetUploadResponse(
        id=asset.id,
        name=asset.name,
        storage_key=asset.storage_key,
        kind=asset.kind.value,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
    )
