"""Unit tests for organization member RBAC and validation."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.services.member_constants import (
    INVITABLE_ROLES,
    MEMBER_ROLES,
    ROLE_PERMISSIONS,
    role_has_permission,
)
from app.services.member_service import MemberService


def test_member_roles_include_eight_types():
    assert len(MEMBER_ROLES) == 8
    assert "organization_owner" in MEMBER_ROLES
    assert "read_only" in MEMBER_ROLES


def test_invitable_roles_exclude_owner():
    assert "organization_owner" not in INVITABLE_ROLES
    assert "auditor" in INVITABLE_ROLES


def test_owner_has_invite_permission():
    assert role_has_permission("organization_owner", "members.invite") is True


def test_auditor_cannot_invite():
    assert role_has_permission("auditor", "members.invite") is False


def test_audit_manager_can_manage_members():
    perms = ROLE_PERMISSIONS["audit_manager"]
    assert "members.invite" in perms
    assert "members.remove" in perms


def test_read_only_has_no_permissions():
    assert ROLE_PERMISSIONS["read_only"] == frozenset()


def test_invite_rejects_invalid_email():
    service = MemberService(
        repository=MagicMock(),
        organization_repository=MagicMock(),
        subscription_repository=MagicMock(),
    )
    db = MagicMock()
    user = MagicMock()
    org_id = uuid.uuid4()
    service.assert_permission = MagicMock()
    service._assert_user_capacity = MagicMock()

    with pytest.raises(ValueError, match="valid email"):
        service.invite_member(
            db, user, org_id, email="not-an-email", role="auditor"
        )


def test_cannot_remove_self():
    service = MemberService(repository=MagicMock())
    db = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()
    org_id = uuid.uuid4()
    member_id = uuid.uuid4()

    member = MagicMock()
    member.organization_id = org_id
    member.user_id = user.id
    service._repo.get_by_id = MagicMock(return_value=member)
    service.assert_permission = MagicMock()

    with pytest.raises(ValueError, match="cannot remove yourself"):
        service.remove_member(db, user, org_id, member_id)
