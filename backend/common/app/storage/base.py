"""Storage backend base for asset persistence."""
from __future__ import annotations

import uuid
from abc import ABC
from abc import abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: BinaryIO | bytes, content_type: str | None = None) -> str:
        """Store object, return storage_key or URL."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> bytes | None:
        """Retrieve object by key."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete object by key."""
        raise NotImplementedError

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Return presigned download URL if supported."""
        return None

    def generate_key(self, tenant_id: str, project_id: str, filename: str) -> str:
        """Generate unique storage key."""
        ext = ""
        if filename and "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1]
        return f"{tenant_id}/{project_id}/{uuid.uuid4().hex}{ext}"
