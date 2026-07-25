"""Unit tests for Phase 2 Milestone 1 — Engagement Team Management."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.engagement_team_constants import (
    ENGAGEMENT_SINGLE_SLOT_ROLES,
    ENGAGEMENT_TEAM_MANAGE_ORG_ROLES,
    ENGAGEMENT_TEAM_ROLES,
    engagement_role_has_permission,
)
from app.services.engagement_team_service import EngagementTeamService


def test_engagement_team_roles_include_five_audit_roles():
    assert len(ENGAGEMENT_TEAM_ROLES) == 5
    assert "partner" in ENGAGEMENT_TEAM_ROLES
    assert "reviewer" in ENGAGEMENT_TEAM_ROLES


def test_single_slot_roles_are_partner_and_manager():
    assert ENGAGEMENT_SINGLE_SLOT_ROLES == frozenset({"partner", "audit_manager"})


def test_partner_can_manage_team():
    assert "partner" in ENGAGEMENT_TEAM_MANAGE_ORG_ROLES


def test_auditor_cannot_manage_team():
    assert "auditor" not in ENGAGEMENT_TEAM_MANAGE_ORG_ROLES


def test_engagement_partner_has_approve_permission():
    assert engagement_role_has_permission("partner", "engagement.approve") is True


def test_engagement_auditor_cannot_approve():
    assert engagement_role_has_permission("auditor", "engagement.approve") is False


def test_assign_rejects_invalid_role():
    service = EngagementTeamService()
    db = MagicMock()
    org_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.member_role = "audit_manager"
    tenant.user.id = uuid.uuid4()
    tenant.organization_id = org_id

    with patch(
        "app.services.engagement_team_service.get_owned_engagement",
        return_value=MagicMock(id=uuid.uuid4(), organization_id=org_id),
    ):
        with pytest.raises(ValueError, match="Invalid engagement team role"):
            service.assign_member(
                db,
                tenant,
                uuid.uuid4(),
                user_id=uuid.uuid4(),
                role="organization_owner",
            )


def test_assign_requires_manage_permission():
    service = EngagementTeamService()
    db = MagicMock()
    tenant = MagicMock()
    tenant.member_role = "auditor"

    with pytest.raises(PermissionError, match="permission"):
        service.assign_member(
            db,
            tenant,
            uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="auditor",
        )


def test_validate_team_role_normalizes():
    assert EngagementTeamService._validate_team_role("  PARTNER ") == "partner"


def test_list_team_rejects_invalid_status():
    service = EngagementTeamService()
    db = MagicMock()
    tenant = MagicMock()

    with patch(
        "app.services.engagement_team_service.get_owned_engagement",
        return_value=MagicMock(id=uuid.uuid4()),
    ):
        with pytest.raises(ValueError, match="Invalid status"):
            service.list_team_members(
                db,
                tenant,
                uuid.uuid4(),
                status="invalid",
            )


def test_history_rejects_invalid_action():
    service = EngagementTeamService()
    db = MagicMock()
    tenant = MagicMock()

    with patch(
        "app.services.engagement_team_service.get_owned_engagement",
        return_value=MagicMock(id=uuid.uuid4()),
    ):
        with pytest.raises(ValueError, match="Invalid action"):
            service.list_assignment_history(
                db,
                tenant,
                uuid.uuid4(),
                action="deleted",
            )


def test_ensure_engagement_organization_requires_engagement_org():
    from datetime import date

    from app.models.audit import AuditEngagement, Client
    from app.services.project_access import ensure_engagement_organization_id

    org_id = uuid.uuid4()
    client = Client(id=uuid.uuid4(), name="Test", user_id=uuid.uuid4(), organization_id=org_id)
    engagement = AuditEngagement(
        id=uuid.uuid4(),
        client_id=client.id,
        client=client,
        organization_id=org_id,
        financial_year="FY 2026-27",
        financial_year_end=date(2027, 3, 31),
    )
    tenant = MagicMock()
    tenant.organization_id = org_id
    db = MagicMock()

    resolved = ensure_engagement_organization_id(db, engagement, tenant)
    assert resolved == org_id


def test_ensure_engagement_organization_rejects_missing_org():
    from datetime import date

    from app.models.audit import AuditEngagement, Client
    from app.services.project_access import ensure_engagement_organization_id

    client = Client(id=uuid.uuid4(), name="Test", user_id=uuid.uuid4(), organization_id=None)
    engagement = AuditEngagement(
        id=uuid.uuid4(),
        client_id=client.id,
        client=client,
        organization_id=None,
        financial_year="FY 2026-27",
        financial_year_end=date(2027, 3, 31),
    )
    tenant = MagicMock()
    tenant.organization_id = uuid.uuid4()
    db = MagicMock()

    with pytest.raises(ValueError, match="not linked to an organization"):
        ensure_engagement_organization_id(db, engagement, tenant)
