"""Resolve report/evidence file references for HTTP download."""

from __future__ import annotations

from pathlib import Path

from app.services.storage import get_storage_backend


def resolve_stored_file(file_ref: str) -> tuple[Path | None, bytes | None]:
    """
    Resolve a DB file reference to either a local Path or in-memory bytes.

    Supports:
    - Absolute/relative filesystem paths from legacy local reports
    - Storage keys (generated_reports/..., reports/..., evidence/..., workpapers/...)
    """
    if not file_ref:
        return None, None

    path = Path(file_ref)
    if path.is_file():
        return path, None

    backend = get_storage_backend()
    key = file_ref.replace("\\", "/")
    if backend.exists(key):
        local = backend.local_path(key)
        if local is not None and local.is_file():
            return local, None
        return None, backend.read(key)

    # Legacy absolute path that no longer exists — try key by basename.
    candidate = f"generated_reports/{path.name}"
    if backend.exists(candidate):
        local = backend.local_path(candidate)
        if local is not None and local.is_file():
            return local, None
        return None, backend.read(candidate)

    return None, None
