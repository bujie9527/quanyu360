"""Asset business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import AssetRepository
from common.app.models import Asset
from common.app.models import AssetKind


class AssetService:
    """Orchestrates asset business logic."""

    def __init__(self, repo: AssetRepository):
        self.repo = repo

    def upload_asset(
        self,
        project_id: UUID,
        tenant_id: UUID,
        filename: str,
        storage_key: str,
        content_type: str | None,
        size_bytes: int,
    ) -> Asset:
        project = self.repo.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        kind = self._infer_kind(filename, content_type)
        asset = Asset(
            tenant_id=tenant_id,
            project_id=project_id,
            name=filename or "unnamed",
            storage_key=storage_key,
            kind=kind,
            mime_type=content_type,
            size_bytes=size_bytes,
        )
        return self.repo.add_asset(asset)

    @staticmethod
    def _infer_kind(filename: str, content_type: str | None) -> AssetKind:
        if content_type and content_type.startswith("image/"):
            return AssetKind.image
        if content_type in ("application/pdf", "text/plain", "text/markdown") or (
            filename and filename.lower().endswith((".pdf", ".md", ".txt"))
        ):
            return AssetKind.document
        return AssetKind.file
