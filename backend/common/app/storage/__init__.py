"""Asset storage backends (S3/MinIO compatible)."""
from common.app.storage.base import StorageBackend
from common.app.storage.s3 import LocalStorage
from common.app.storage.s3 import S3Storage
from common.app.storage.s3 import _get_storage

__all__ = ["StorageBackend", "S3Storage", "LocalStorage", "get_storage"]


def get_storage() -> StorageBackend:
    return _get_storage()
