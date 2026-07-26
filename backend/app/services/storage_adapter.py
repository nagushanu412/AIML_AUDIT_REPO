"""Compatibility layer over StorageBackend (Phase 2 name: BlobStorageAdapter)."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.services.file_storage_service import compute_file_hash
from app.services.storage import (
    LocalDiskStorageBackend,
    StorageBackend,
    get_storage_backend,
)

# Historical names expected by tests and older imports.
BlobStorageAdapter = StorageBackend
LocalBlobStorageAdapter = LocalDiskStorageBackend
get_storage_adapter = get_storage_backend


def save_report_artifact(
    engagement_id: uuid.UUID,
    report_id: uuid.UUID,
    file_name: str,
    content: bytes,
) -> tuple[str, str]:
    ext = Path(file_name).suffix.lower() or ".xlsx"
    key = f"reports/{engagement_id}/{report_id}{ext}"
    get_storage_backend().save(key, content)
    return key, compute_file_hash(content)
