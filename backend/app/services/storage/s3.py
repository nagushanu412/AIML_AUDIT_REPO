from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.storage.backend import StorageBackend, StorageConfigurationError


class S3CompatibleStorageBackend(StorageBackend):
    """S3-compatible object storage (AWS S3, Cloudflare R2, etc.)."""

    def __init__(
        self,
        *,
        bucket: str,
        client: Any,
    ) -> None:
        if not bucket:
            raise StorageConfigurationError(
                "STORAGE_BACKEND=s3 requires S3_BUCKET (or STORAGE_S3_BUCKET) to be set."
            )
        self.bucket = bucket
        self.client = client

    @classmethod
    def from_env(
        cls,
        *,
        bucket: str | None,
        region: str | None,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> S3CompatibleStorageBackend:
        missing: list[str] = []
        if not bucket:
            missing.append("S3_BUCKET")
        if not access_key_id:
            missing.append("AWS_ACCESS_KEY_ID (or S3_ACCESS_KEY_ID)")
        if not secret_access_key:
            missing.append("AWS_SECRET_ACCESS_KEY (or S3_SECRET_ACCESS_KEY)")
        if missing:
            raise StorageConfigurationError(
                "STORAGE_BACKEND=s3 is selected but required configuration is missing: "
                + ", ".join(missing)
                + ". Set these environment variables, or set STORAGE_BACKEND=local."
            )
        try:
            import boto3
        except ImportError as exc:
            raise StorageConfigurationError(
                "STORAGE_BACKEND=s3 requires the 'boto3' package. "
                "Install backend requirements or set STORAGE_BACKEND=local."
            ) from exc

        client_kwargs: dict[str, Any] = {
            "service_name": "s3",
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
            "region_name": region or "us-east-1",
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        client = boto3.client(**client_kwargs)
        return cls(bucket=bucket or "", client=client)

    def save(self, key: str, content: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return key

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"].read()
        return body if isinstance(body, (bytes, bytearray)) else bytes(body)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def local_path(self, key: str) -> Path | None:
        return None
