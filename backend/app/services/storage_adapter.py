from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import get_settings
from app.services.file_storage_service import (
    EVIDENCE_DIR,
    WORKPAPERS_DIR,
    compute_file_hash,
    resolve_storage_path,
)


class BlobStorageAdapter(ABC):
    @abstractmethod
    def save(self, key: str, content: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def resolve_path(self, key: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError


class LocalBlobStorageAdapter(BlobStorageAdapter):
    def save(self, key: str, content: bytes) -> str:
        path = self.resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def resolve_path(self, key: str) -> Path:
        return resolve_storage_path(key)

    def exists(self, key: str) -> bool:
        try:
            return self.resolve_path(key).is_file()
        except ValueError:
            return False


class S3BlobStorageAdapter(BlobStorageAdapter):
    """AWS S3 adapter stub — configure bucket in Milestone 6 production deploy."""

    def save(self, key: str, content: bytes) -> str:
        raise NotImplementedError(
            "S3 storage is not configured. Set STORAGE_BACKEND=local or configure AWS credentials."
        )

    def resolve_path(self, key: str) -> Path:
        raise NotImplementedError("S3 storage does not expose local paths.")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("S3 storage is not configured.")


def get_storage_adapter() -> BlobStorageAdapter:
    backend = getattr(get_settings(), "storage_backend", "local")
    if backend == "local":
        return LocalBlobStorageAdapter()
    if backend in {"s3", "aws"}:
        return S3BlobStorageAdapter()
    return LocalBlobStorageAdapter()


def save_report_artifact(
    engagement_id: uuid.UUID,
    report_id: uuid.UUID,
    file_name: str,
    content: bytes,
) -> tuple[str, str]:
    ext = Path(file_name).suffix.lower() or ".xlsx"
    key = f"reports/{engagement_id}/{report_id}{ext}"
    adapter = get_storage_adapter()
    if isinstance(adapter, LocalBlobStorageAdapter):
        reports_dir = Path(__file__).resolve().parents[2] / "storage" / "reports" / str(engagement_id)
        reports_dir.mkdir(parents=True, exist_ok=True)
        path = reports_dir / f"{report_id}{ext}"
        path.write_bytes(content)
        return key, compute_file_hash(content)
    adapter.save(key, content)
    return key, compute_file_hash(content)
