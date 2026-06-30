from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.config import get_settings

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"
EVIDENCE_DIR = STORAGE_ROOT / "evidence"
WORKPAPERS_DIR = STORAGE_ROOT / "workpapers"

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


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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

    target_dir = EVIDENCE_DIR / str(engagement_id)
    _ensure_dir(target_dir)
    safe_name = f"{evidence_id}{ext}"
    target_path = target_dir / safe_name
    target_path.write_bytes(content)

    storage_key = f"evidence/{engagement_id}/{safe_name}"
    file_hash = compute_file_hash(content)
    return storage_key, file_hash


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

    target_dir = WORKPAPERS_DIR / str(engagement_id)
    _ensure_dir(target_dir)
    safe_name = f"{workpaper_id}{ext}"
    target_path = target_dir / safe_name
    target_path.write_bytes(content)

    storage_key = f"workpapers/{engagement_id}/{safe_name}"
    file_hash = compute_file_hash(content)
    return storage_key, file_hash


def resolve_storage_path(storage_key: str) -> Path:
    """Resolve a storage key to absolute filesystem path (local adapter)."""
    if storage_key.startswith("evidence/"):
        relative = storage_key.removeprefix("evidence/")
        return EVIDENCE_DIR / relative
    if storage_key.startswith("workpapers/"):
        relative = storage_key.removeprefix("workpapers/")
        return WORKPAPERS_DIR / relative
    raise ValueError("Invalid storage key.")


def file_exists(storage_key: str) -> bool:
    try:
        return resolve_storage_path(storage_key).is_file()
    except ValueError:
        return False
