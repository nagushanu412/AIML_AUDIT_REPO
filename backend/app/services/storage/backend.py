"""Swappable blob storage backends (Constitution §7.7 / Remediation M5 Part A)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageConfigurationError(RuntimeError):
    """Raised when a non-local backend is selected but not properly configured."""


class StorageBackend(ABC):
    """Operations required by evidence, workpaper, and report call sites."""

    @abstractmethod
    def save(self, key: str, content: bytes) -> str:
        """Persist bytes at key; return the same key."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Return file bytes for key."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """True if an object exists at key."""

    @abstractmethod
    def local_path(self, key: str) -> Path | None:
        """Absolute filesystem path when the object is on local disk; else None."""

    def reference_for_db(self, key: str) -> str:
        """Value stored on Report.file_path (absolute path locally, key for object stores)."""
        path = self.local_path(key)
        return str(path) if path is not None else key
