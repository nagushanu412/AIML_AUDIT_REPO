"""Unit tests for Phase 2 Milestone 2 — Evidence & Workpapers."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.evidence_constants import EVIDENCE_CATEGORIES, LINK_TYPES
from app.services.evidence_service import EvidenceService
from app.services.file_storage_service import compute_file_hash
from app.services.workpaper_constants import WORKPAPER_CATEGORIES
from app.services.workpaper_service import WorkpaperService


def test_evidence_categories_defined():
    assert "invoice" in EVIDENCE_CATEGORIES
    assert "other" in EVIDENCE_CATEGORIES


def test_workpaper_categories_defined():
    assert "testing" in WORKPAPER_CATEGORIES
    assert "planning" in WORKPAPER_CATEGORIES


def test_file_hash_is_sha256_hex():
    digest = compute_file_hash(b"test-content")
    assert len(digest) == 64


def test_evidence_upload_rejects_invalid_category():
    service = EvidenceService()
    tenant = MagicMock()
    tenant.member_role = "auditor"
    tenant.user.id = uuid.uuid4()
    tenant.organization_id = uuid.uuid4()

    with patch(
        "app.services.evidence_service.get_owned_engagement",
        return_value=MagicMock(id=uuid.uuid4(), organization_id=tenant.organization_id),
    ):
        with pytest.raises(ValueError, match="Invalid category"):
            service.upload_evidence(
                MagicMock(),
                tenant,
                uuid.uuid4(),
                file_name="doc.pdf",
                content=b"x",
                content_type="application/pdf",
                title="Test",
                category="invalid",
            )


def test_evidence_manage_requires_role():
    service = EvidenceService()
    tenant = MagicMock()
    tenant.member_role = "read_only"

    with pytest.raises(PermissionError, match="permission"):
        service.upload_evidence(
            MagicMock(),
            tenant,
            uuid.uuid4(),
            file_name="doc.pdf",
            content=b"x",
            content_type="application/pdf",
            title="Test",
        )


def test_workpaper_create_requires_reference():
    service = WorkpaperService()
    tenant = MagicMock()
    tenant.member_role = "auditor"
    tenant.user.id = uuid.uuid4()
    tenant.organization_id = uuid.uuid4()

    with patch(
        "app.services.workpaper_service.get_owned_engagement",
        return_value=MagicMock(id=uuid.uuid4(), organization_id=tenant.organization_id),
    ):
        with pytest.raises(ValueError, match="Reference code"):
            service.create_workpaper(
                MagicMock(),
                tenant,
                uuid.uuid4(),
                reference_code="  ",
                title="Test WP",
            )


def test_link_types_include_supports():
    assert "supports" in LINK_TYPES
