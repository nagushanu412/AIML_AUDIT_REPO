from app.services.storage.backend import StorageBackend, StorageConfigurationError
from app.services.storage.factory import get_storage_backend, reset_storage_backend_cache
from app.services.storage.local import LocalDiskStorageBackend
from app.services.storage.s3 import S3CompatibleStorageBackend

# Backward-compatible aliases used by Phase 2 tests / imports.
LocalBlobStorageAdapter = LocalDiskStorageBackend
get_storage_adapter = get_storage_backend

__all__ = [
    "StorageBackend",
    "StorageConfigurationError",
    "LocalDiskStorageBackend",
    "S3CompatibleStorageBackend",
    "get_storage_backend",
    "reset_storage_backend_cache",
    "LocalBlobStorageAdapter",
    "get_storage_adapter",
]
