"""S3/MinIO compatible storage backend."""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

from common.app.storage.base import StorageBackend


def _get_storage() -> StorageBackend:
    """Return S3Storage if configured, else LocalStorage fallback."""
    if os.getenv("S3_ENDPOINT_URL") or os.getenv("S3_BUCKET"):
        return S3Storage()
    return LocalStorage(base_path=os.getenv("ASSET_STORAGE_PATH", "/tmp/assets"))


class LocalStorage(StorageBackend):
    """Local filesystem fallback when S3 not configured."""

    def __init__(self, base_path: str = "/tmp/assets") -> None:
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: BinaryIO | bytes, content_type: str | None = None) -> str:
        path = self.base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        body = data.read() if hasattr(data, "read") else data
        path.write_bytes(body)
        return key

    def get(self, key: str) -> bytes | None:
        path = self.base / key
        if not path.exists():
            return None
        return path.read_bytes()

    def delete(self, key: str) -> bool:
        path = self.base / key
        if path.exists():
            path.unlink()
        return True


class S3Storage(StorageBackend):
    """S3-compatible storage. Requires boto3 or aioboto3 for presigned URLs."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        bucket: str = "assets",
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self.bucket = bucket or os.getenv("S3_BUCKET", "assets")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        self._client = None

    def _get_client(self):
        try:
            import boto3
            from botocore.config import Config

            return boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4"),
            )
        except ImportError:
            return None

    def put(self, key: str, data: BinaryIO | bytes, content_type: str | None = None) -> str:
        client = self._get_client()
        if not client:
            return f"local://{key}"
        body = data.read() if hasattr(data, "read") else data
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        client.put_object(Bucket=self.bucket, Key=key, Body=body, **extra)
        return key

    def get(self, key: str) -> bytes | None:
        client = self._get_client()
        if not client:
            return None
        try:
            resp = client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except client.exceptions.NoSuchKey:
            return None

    def delete(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return True
        try:
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str | None:
        client = self._get_client()
        if not client:
            return None
        try:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception:
            return None

