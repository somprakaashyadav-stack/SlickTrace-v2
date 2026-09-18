"""
SlickTrace v2 — MinIO / S3-compatible object storage client.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageClient:
    def __init__(self):
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self._ensure_buckets()

    def _ensure_buckets(self) -> None:
        for bucket in [
            settings.MINIO_BUCKET_IMAGERY,
            settings.MINIO_BUCKET_OUTPUTS,
            settings.MINIO_BUCKET_DOSSIERS,
        ]:
            try:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info(f"[STORAGE] Created bucket: {bucket}")
            except Exception as e:
                logger.warning(f"[STORAGE] Object storage not reachable at {settings.MINIO_ENDPOINT}: {e}")

    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self._client.put_object(
            bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"s3://{bucket}/{key}"

    def upload_file(self, bucket: str, key: str, file_path: Path) -> str:
        self._client.fput_object(bucket, key, str(file_path))
        return f"s3://{bucket}/{key}"

    def download_bytes(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(bucket, key)
        data = response.read()
        response.close()
        response.release_conn()
        return data

    def get_presigned_url(self, bucket: str, key: str, expires_hours: int = 1) -> str:
        from datetime import timedelta
        return self._client.presigned_get_object(
            bucket, key, expires=timedelta(hours=expires_hours)
        )


_storage_client: Optional[StorageClient] = None


def get_storage() -> StorageClient:
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
