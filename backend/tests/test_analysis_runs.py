"""Tests for analysis runs and storage adapter."""

from app.services.analysis_run_service import RUN_STATUSES, SUGGESTED_RUN_NAMES
from app.services.storage_adapter import LocalBlobStorageAdapter, get_storage_adapter


def test_run_statuses_include_lifecycle():
    assert "draft" in RUN_STATUSES
    assert "locked" in RUN_STATUSES


def test_suggested_run_names():
    assert "Initial Submission" in SUGGESTED_RUN_NAMES


def test_local_storage_adapter_default():
    adapter = get_storage_adapter()
    assert isinstance(adapter, LocalBlobStorageAdapter)
