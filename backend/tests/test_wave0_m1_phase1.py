"""Wave 0 Milestone 1 — Phase 1 closeout tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.audit import Client
from app.services.auth_service import register_user
from app.services.project_access import _client_accessible, client_list_filter
from app.services.tenant_context import TenantContext


def test_register_user_can_create_organization():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    user = MagicMock()
    user.id = uuid.uuid4()
    user.default_organization_id = uuid.uuid4()

    with patch("app.services.auth_service.User", return_value=user):
        with patch("app.services.organization_service.OrganizationService") as org_cls:
            org_cls.return_value.create_organization.return_value = MagicMock()
            register_user(
                db,
                email="new@firm.com",
                password="password123",
                full_name="New Auditor",
                company_name="New Firm LLP",
                create_organization=True,
            )
    org_cls.return_value.create_organization.assert_called_once()


def test_org_scoped_client_access_denies_other_org():
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=org_a, member_role="auditor")

    client = MagicMock()
    client.organization_id = org_b
    client.user_id = user.id

    assert _client_accessible(client, tenant) is False


def test_org_scoped_client_access_allows_same_org():
    org_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=org_id, member_role="auditor")

    client = MagicMock()
    client.organization_id = org_id
    client.user_id = uuid.uuid4()

    assert _client_accessible(client, tenant) is True


def test_client_list_filter_org_only_when_tenant_has_org():
    org_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=org_id, member_role="auditor")
    clause = client_list_filter(tenant)
    compiled = str(clause)
    assert "organization_id" in compiled
    assert "user_id" not in compiled


def test_client_list_filter_user_fallback_without_org():
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=None, member_role=None)
    clause = client_list_filter(tenant)
    compiled = str(clause)
    assert "user_id" in compiled


def test_demo_organization_seed_function_exists():
    from app.services.seed_service import ensure_demo_organization

    assert callable(ensure_demo_organization)
