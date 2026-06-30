"""Unit tests for organization slug helpers and validation."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.services.organization_service import (
    OrganizationService,
    generate_unique_slug,
    slugify_name,
    validate_slug,
    validate_status,
)


def test_slugify_name_basic():
    assert slugify_name("ABC & Co Chartered Accountants") == "abc-co-chartered-accountants"


def test_slugify_name_empty_fallback():
    assert slugify_name("!!!") == "organization"


def test_validate_slug_accepts_valid():
    validate_slug("abc-co-123")


def test_validate_slug_rejects_invalid():
    with pytest.raises(ValueError, match="lowercase"):
        validate_slug("ABC Co")


def test_validate_status_rejects_unknown():
    with pytest.raises(ValueError, match="Invalid status"):
        validate_status("deleted")


def test_generate_unique_slug_appends_suffix():
    db = MagicMock()
    repo = MagicMock()
    repo.slug_exists = MagicMock(side_effect=[True, False])
    slug = generate_unique_slug(db, repo, "ABC & Co")
    assert slug.endswith("-2")


def test_create_organization_requires_name_length():
    member_service = MagicMock()
    member_service.user_has_active_membership.return_value = False
    service = OrganizationService(repository=MagicMock(), member_service=member_service)
    db = MagicMock()
    user = MagicMock()
    user.default_organization_id = None
    with pytest.raises(ValueError, match="at least 2 characters"):
        service.create_organization(db, user, name="A")


def test_assert_access_denied_for_other_org():
    service = OrganizationService(repository=MagicMock())
    db = MagicMock()
    user = MagicMock()
    user.default_organization_id = uuid.uuid4()
    other_id = uuid.uuid4()
    with pytest.raises(PermissionError):
        service.get_organization_for_user(db, user, other_id)
