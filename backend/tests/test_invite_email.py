"""Tests for invite tokens and email helpers."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.invite_service import (
    build_invite_link,
    create_invite_token,
    decode_invite_token,
    preview_invite,
    send_member_invite_email,
)


def test_create_and_decode_invite_token():
    member_id = uuid.uuid4()
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()

    token = create_invite_token(
        member_id=member_id,
        user_id=user_id,
        organization_id=org_id,
        email="invitee@firm.com",
        is_new_user=True,
    )

    payload = decode_invite_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["member_id"] == str(member_id)
    assert payload["org_id"] == str(org_id)
    assert payload["email"] == "invitee@firm.com"
    assert payload["is_new_user"] is True
    assert payload["type"] == "invite"


def test_build_invite_link_contains_token():
    token = "sample-token"
    link = build_invite_link(token)
    assert link.endswith(f"/accept-invite?token={token}")


@patch("app.services.invite_service.send_email")
def test_send_member_invite_email_returns_link_when_smtp_not_configured(mock_send_email):
    mock_send_email.return_value = MagicMock(sent=False, logged_to_console=True)

    db = MagicMock()
    organization = MagicMock()
    organization.name = "Demo Audit Firm"
    db.query.return_value.filter.return_value.first.return_value = organization

    member = MagicMock()
    member.id = uuid.uuid4()
    member.organization_id = uuid.uuid4()
    member.role = "auditor"
    member.user = MagicMock(email="invitee@firm.com", full_name="Invitee User")

    inviter = MagicMock(full_name="Owner User")

    result = send_member_invite_email(
        db,
        member,
        inviter=inviter,
        is_new_user=True,
    )

    assert result.sent is False
    assert result.invite_link is not None
    assert "accept-invite?token=" in result.invite_link


def test_preview_invite_rejects_invalid_token():
    db = MagicMock()
    with pytest.raises(ValueError, match="invalid or has expired"):
        preview_invite(db, "not-a-valid-token")
