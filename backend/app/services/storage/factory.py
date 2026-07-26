from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.services.storage.backend import StorageBackend, StorageConfigurationError
from app.services.storage.local import LocalDiskStorageBackend
from app.services.storage.s3 import S3CompatibleStorageBackend


@lru_cache
def get_storage_backend() -> StorageBackend:
    """Return the configured storage backend (default: local disk)."""
    settings = get_settings()
    backend = (settings.storage_backend or "local").strip().lower()

    if backend == "local":
        return LocalDiskStorageBackend()

    if backend in {"s3", "aws"}:
        return S3CompatibleStorageBackend.from_env(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
        )

    raise StorageConfigurationError(
        f"Unknown STORAGE_BACKEND={backend!r}. Use 'local' or 's3'."
    )


def reset_storage_backend_cache() -> None:
    """Test helper — clear cached backend selection."""
    get_storage_backend.cache_clear()
