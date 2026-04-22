"""
Object storage service for appointment files (MinIO/S3-compatible).
"""

from __future__ import annotations

import io
from datetime import datetime
from uuid import uuid4, UUID
from urllib.parse import quote

from minio import Minio
from minio.error import S3Error

from app.config import settings


class StorageService:
    """Handles file operations against MinIO bucket."""

    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket_name

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_appointment_file(
        self,
        appointment_id: UUID,
        original_name: str,
        content: bytes,
        content_type: str | None,
    ) -> str:
        """Upload file content and return object path in format bucket/key."""
        self.ensure_bucket()

        ext = ""
        if "." in original_name:
            ext = "." + original_name.rsplit(".", 1)[-1].lower()

        object_key = (
            f"appointments/{appointment_id}/{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
            f"_{uuid4().hex}{ext}"
        )

        data_stream = io.BytesIO(content)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=data_stream,
            length=len(content),
            content_type=content_type or "application/octet-stream",
        )

        return f"{self.bucket}/{object_key}"

    def presigned_download_url(self, minio_path: str, expires_seconds: int = 900) -> str:
        """Create presigned GET URL from stored path formatted as bucket/key."""
        if "/" not in minio_path:
            raise ValueError("Invalid minio path")

        bucket, object_key = minio_path.split("/", 1)
        if bucket != self.bucket:
            raise ValueError("Bucket mismatch")

        return self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expires_seconds,
            response_headers={
                "response-content-disposition": f'attachment; filename="{quote(object_key.rsplit("/", 1)[-1])}"'
            },
        )


storage_service = StorageService()
