"""Remediation Milestone 5 Part A Step 2 — swappable storage backends."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.file_storage_service import (
    file_exists,
    resolve_storage_path,
    save_evidence_file,
    save_workpaper_file,
)
from app.services.storage import (
    LocalDiskStorageBackend,
    S3CompatibleStorageBackend,
    StorageConfigurationError,
    get_storage_backend,
    reset_storage_backend_cache,
)
from app.services.storage.factory import get_storage_backend as factory_get
from app.services.storage_adapter import save_report_artifact


@pytest.fixture(autouse=True)
def _clear_backend_cache():
    reset_storage_backend_cache()
    yield
    reset_storage_backend_cache()


def test_default_backend_is_local_disk():
    backend = get_storage_backend()
    assert isinstance(backend, LocalDiskStorageBackend)


def test_local_backend_save_read_exists_roundtrip(tmp_path: Path):
    backend = LocalDiskStorageBackend(root=tmp_path / "storage", generated_reports=tmp_path / "generated")
    key = "evidence/eng-1/file.bin"
    backend.save(key, b"hello-local")
    assert backend.exists(key)
    assert backend.read(key) == b"hello-local"
    path = backend.local_path(key)
    assert path is not None
    assert path.read_bytes() == b"hello-local"
    assert backend.reference_for_db(key) == str(path)


def test_save_evidence_and_workpaper_go_through_backend(tmp_path: Path, monkeypatch):
    import uuid

    root = tmp_path / "storage"
    gen = tmp_path / "generated"
    backend = LocalDiskStorageBackend(root=root, generated_reports=gen)

    monkeypatch.setattr(
        "app.services.file_storage_service.get_storage_backend", lambda: backend
    )
    monkeypatch.setattr(
        "app.services.storage_adapter.get_storage_backend", lambda: backend
    )

    eng = uuid.uuid4()
    eid = uuid.uuid4()
    wid = uuid.uuid4()
    rid = uuid.uuid4()

    ekey, ehash = save_evidence_file(eng, eid, "note.txt", b"evidence-bytes")
    wkey, whash = save_workpaper_file(eng, wid, "wp.txt", b"workpaper-bytes")
    rkey, rhash = save_report_artifact(eng, rid, "report.json", b'{"ok":true}')

    assert ekey.startswith("evidence/")
    assert wkey.startswith("workpapers/")
    assert rkey.startswith("reports/")
    assert len(ehash) == 64 and len(whash) == 64 and len(rhash) == 64
    assert backend.read(ekey) == b"evidence-bytes"
    assert backend.read(wkey) == b"workpaper-bytes"
    assert backend.read(rkey) == b'{"ok":true}'
    assert file_exists(ekey)
    assert resolve_storage_path(ekey).is_file()


def test_s3_backend_requires_explicit_config():
    with pytest.raises(StorageConfigurationError, match="required configuration is missing"):
        S3CompatibleStorageBackend.from_env(
            bucket=None,
            region=None,
            endpoint_url=None,
            access_key_id=None,
            secret_access_key=None,
        )


def test_s3_backend_with_mocked_client():
    client = MagicMock()
    store: dict[str, bytes] = {}

    def put_object(*, Bucket, Key, Body):
        store[Key] = Body
        return {}

    def get_object(*, Bucket, Key):
        body = MagicMock()
        body.read.return_value = store[Key]
        return {"Body": body}

    def head_object(*, Bucket, Key):
        if Key not in store:
            raise client.exceptions.NoSuchKey({}, "HeadObject")  # type: ignore[attr-defined]
        return {}

    client.put_object.side_effect = put_object
    client.get_object.side_effect = get_object
    # head_object: raise on missing
    def _head(*, Bucket, Key):
        if Key not in store:
            raise RuntimeError("404")
        return {}

    client.head_object.side_effect = _head

    backend = S3CompatibleStorageBackend(bucket="audit-bucket", client=client)
    key = "evidence/e1/a.txt"
    backend.save(key, b"s3-bytes")
    assert backend.exists(key)
    assert backend.read(key) == b"s3-bytes"
    assert backend.local_path(key) is None
    assert backend.reference_for_db(key) == key


def test_factory_s3_does_not_silently_fallback_to_local(monkeypatch):
    class _Settings:
        storage_backend = "s3"
        s3_bucket = None
        s3_region = None
        s3_endpoint_url = None
        s3_access_key_id = None
        s3_secret_access_key = None

    monkeypatch.setattr("app.services.storage.factory.get_settings", lambda: _Settings())
    reset_storage_backend_cache()
    with pytest.raises(StorageConfigurationError, match="STORAGE_BACKEND=s3"):
        factory_get()
