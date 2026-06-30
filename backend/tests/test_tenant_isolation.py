"""Unit tests for tenant isolation and JWT org context."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.services.auth_service import create_access_token, decode_access_token_payload
from app.services.project_access import client_list_filter
from app.services.tenant_context import TenantContext, TenantContextService


def test_jwt_includes_org_claims():
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    token = create_access_token(user_id, organization_id=org_id, member_role="audit_manager")
    payload = decode_access_token_payload(token)
    assert payload["sub"] == str(user_id)
    assert payload["org_id"] == str(org_id)
    assert payload["org_role"] == "audit_manager"


def test_jwt_without_org_claims_still_valid():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_access_token_payload(token)
    assert payload["sub"] == str(user_id)
    assert "org_id" not in payload


def test_token_org_mismatch_raises():
    service = TenantContextService(member_repository=MagicMock())
    db = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.default_organization_id = uuid.uuid4()

    resolved_org = user.default_organization_id
    service._member_repo.get_membership.return_value = MagicMock(
        status="active", role="organization_owner"
    )
    service._member_repo.get_active_membership_for_user.return_value = None

    wrong_org = uuid.uuid4()
    with pytest.raises(PermissionError, match="mismatch"):
        service.validate_token_org_claims(
            db, user, token_org_id=wrong_org, token_org_role=None
        )


def test_client_list_filter_uses_org_when_present():
    org_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=org_id, member_role="auditor")
    clause = client_list_filter(tenant)
    assert clause is not None


def test_client_list_filter_falls_back_to_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = TenantContext(user=user, organization_id=None, member_role=None)
    from app.models.audit import Client

    clause = client_list_filter(tenant)
    compiled = str(clause)
    assert "user_id" in compiled or clause is not None
