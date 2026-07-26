from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.config import get_settings
from app.services.storage import get_storage_backend
from app.services.storage.local import GENERATED_REPORTS_DIR, STORAGE_ROOT

# Re-export historical constants for any imports that still expect them.
EVIDENCE_DIR = STORAGE_ROOT / "evidence"
WORKPAPERS_DIR = STORAGE_ROOT / "workpapers"
REPORTS_DIR = STORAGE_ROOT / "reports"

ALLOWED_EVIDENCE_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".xlsx",
        ".xls",
        ".csv",
        ".doc",
        ".docx",
        ".txt",
        ".zip",
    }
)

ALLOWED_WORKPAPER_EXTENSIONS = ALLOWED_EVIDENCE_EXTENSIONS


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def save_evidence_file(
    engagement_id: uuid.UUID,
    evidence_id: uuid.UUID,
    file_name: str,
    content: bytes,
) -> tuple[str, str]:
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File too large. Maximum size is {settings.max_upload_mb} MB."
        )

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EVIDENCE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EVIDENCE_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed: {allowed}")

    safe_name = f"{evidence_id}{ext}"
    storage_key = f"evidence/{engagement_id}/{safe_name}"
    get_storage_backend().save(storage_key, content)
    return storage_key, compute_file_hash(content)


def save_workpaper_file(
    engagement_id: uuid.UUID,
    workpaper_id: uuid.UUID,
    file_name: str,
    content: bytes,
) -> tuple[str, str]:
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File too large. Maximum size is {settings.max_upload_mb} MB."
        )

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_WORKPAPER_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_WORKPAPER_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed: {allowed}")

    safe_name = f"{workpaper_id}{ext}"
    storage_key = f"workpapers/{engagement_id}/{safe_name}"
    get_storage_backend().save(storage_key, content)
    return storage_key, compute_file_hash(content)


def resolve_storage_path(storage_key: str) -> Path:
    """Resolve a storage key to a local filesystem path (local backend only)."""
    backend = get_storage_backend()
    path = backend.local_path(storage_key)
    if path is None:
        raise ValueError(
            "Storage key cannot be resolved to a local path with the active backend. "
            "Use storage.read() for object-store backends."
        )
    # Preserve historical validation for unexpected key prefixes on local layout.
    if not (
        storage_key.startswith("evidence/")
        or storage_key.startswith("workpapers/")
        or storage_key.startswith("reports/")
        or storage_key.startswith("generated_reports/")
    ):
        raise ValueError("Invalid storage key.")
    return path


def file_exists(storage_key: str) -> bool:
    try:
        if not (
            storage_key.startswith("evidence/")
            or storage_key.startswith("workpapers/")
            or storage_key.startswith("reports/")
            or storage_key.startswith("generated_reports/")
        ):
            return False
        return get_storage_backend().exists(storage_key)
    except ValueError:
        return False


def read_storage_bytes(storage_key: str) -> bytes:
    return get_storage_backend().read(storage_key)


# Keep import surface for report_export migration notes.
__all__ = [
    "ALLOWED_EVIDENCE_EXTENSIONS",
    "ALLOWED_WORKPAPER_EXTENSIONS",
    "EVIDENCE_DIR",
    "WORKPAPERS_DIR",
    "REPORTS_DIR",
    "GENERATED_REPORTS_DIR",
    "STORAGE_ROOT",
    "compute_file_hash",
    "save_evidence_file",
    "save_workpaper_file",
    "resolve_storage_path",
    "file_exists",
    "read_storage_bytes",
]
