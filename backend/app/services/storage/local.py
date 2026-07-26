from __future__ import annotations

from pathlib import Path

from app.services.storage.backend import StorageBackend

# Same roots as the pre-M5 file_storage_service / report_export layout.
STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage"
GENERATED_REPORTS_DIR = Path(__file__).resolve().parents[3] / "generated_reports"


class LocalDiskStorageBackend(StorageBackend):
    """Local disk backend preserving historical directory layout."""

    def __init__(self, root: Path | None = None, generated_reports: Path | None = None) -> None:
        self.root = root or STORAGE_ROOT
        self.generated_reports = generated_reports or GENERATED_REPORTS_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self.generated_reports.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        key = key.replace("\\", "/").lstrip("/")
        if ".." in key.split("/"):
            raise ValueError("Invalid storage key.")
        if key.startswith("generated_reports/"):
            relative = key.removeprefix("generated_reports/")
            return self.generated_reports / relative
        return self.root / key

    def save(self, key: str, content: bytes) -> str:
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def read(self, key: str) -> bytes:
        path = self._path_for_key(key)
        if not path.is_file():
            raise FileNotFoundError(f"Storage object not found: {key}")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        try:
            return self._path_for_key(key).is_file()
        except ValueError:
            return False

    def local_path(self, key: str) -> Path | None:
        # Local backend always has a filesystem path for a key (may not exist yet).
        return self._path_for_key(key)
