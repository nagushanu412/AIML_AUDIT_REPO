"""Remediation Milestone 3 Step 1 — reviewed_by / reviewed_at on status transitions."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.finding_lifecycle_service import FindingLifecycleService


def _tenant(*, role: str = "partner") -> MagicMock:
    tenant = MagicMock()
    tenant.member_role = role
    tenant.user.id = uuid.uuid4()
    return tenant


def _finding(*, status: str = "open") -> MagicMock:
    finding = MagicMock()
    finding.id = uuid.uuid4()
    finding.project_id = uuid.uuid4()
    finding.status = status
    finding.reviewed_by = None
    finding.reviewed_at = None
    finding.updated_by = None
    return finding


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
def test_decision_status_sets_reviewed_by_and_reviewed_at(mock_guard):
    service = FindingLifecycleService()
    finding = _finding(status="under_review")
    tenant = _tenant()
    db = MagicMock()

    with (
        patch.object(service, "_get_owned_finding", return_value=finding),
        patch.object(service, "_write_history"),
        patch.object(service, "_load", return_value=finding),
    ):
        result = service.update_status(
            db, tenant, finding.id, status="cleared", change_reason="ok"
        )

    assert result is finding
    assert finding.status == "cleared"
    assert finding.reviewed_by == tenant.user.id
    assert isinstance(finding.reviewed_at, datetime)
    assert finding.reviewed_at.tzinfo is not None
    mock_guard.assert_called_once_with(db, finding.project_id)


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
@pytest.mark.parametrize("new_status", ["open", "under_review"])
def test_pre_decision_status_keeps_reviewed_fields_null(mock_guard, new_status: str):
    service = FindingLifecycleService()
    # Start from a status that can reach open / under_review
    current = "closed" if new_status == "open" else "accepted"
    finding = _finding(status=current)
    finding.reviewed_by = uuid.uuid4()
    finding.reviewed_at = datetime.utcnow()
    tenant = _tenant(role="partner")
    db = MagicMock()

    with (
        patch.object(service, "_get_owned_finding", return_value=finding),
        patch.object(service, "_write_history"),
        patch.object(service, "_load", return_value=finding),
    ):
        service.update_status(
            db, tenant, finding.id, status=new_status, change_reason="reopen/review"
        )

    assert finding.status == new_status
    assert finding.reviewed_by is None
    assert finding.reviewed_at is None


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
def test_open_to_under_review_leaves_reviewed_null(mock_guard):
    service = FindingLifecycleService()
    finding = _finding(status="open")
    tenant = _tenant(role="auditor")
    db = MagicMock()

    with (
        patch.object(service, "_get_owned_finding", return_value=finding),
        patch.object(service, "_write_history"),
        patch.object(service, "_load", return_value=finding),
    ):
        service.update_status(
            db, tenant, finding.id, status="under_review", change_reason=None
        )

    assert finding.status == "under_review"
    assert finding.reviewed_by is None
    assert finding.reviewed_at is None


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
def test_close_then_reopen_nulls_reviewed_fields(mock_guard):
    """Closing stamps reviewer; closed → open clears both (Constitution §6.10)."""
    service = FindingLifecycleService()
    finding = _finding(status="open")
    tenant = _tenant(role="partner")
    db = MagicMock()

    with (
        patch.object(service, "_get_owned_finding", return_value=finding),
        patch.object(service, "_write_history"),
        patch.object(service, "_load", return_value=finding),
    ):
        service.update_status(db, tenant, finding.id, status="closed")
        assert finding.status == "closed"
        assert finding.reviewed_by == tenant.user.id
        assert isinstance(finding.reviewed_at, datetime)

        service.update_status(db, tenant, finding.id, status="open", change_reason="reopen")
        assert finding.status == "open"
        assert finding.reviewed_by is None
        assert finding.reviewed_at is None


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
def test_partner_approval_sets_reviewed_fields(mock_guard):
    from app.services.review_workflow_service import ReviewWorkflowService

    service = ReviewWorkflowService()
    finding_id = uuid.uuid4()
    finding = _finding(status="under_review")
    finding.id = finding_id
    tenant = _tenant(role="partner")
    approval = MagicMock()
    approval.engagement_id = uuid.uuid4()
    approval.finding_id = finding_id
    approval.comments = None
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [approval, finding]

    with (
        patch(
            "app.services.review_workflow_service.get_owned_engagement",
            return_value=MagicMock(),
        ),
        patch.object(service, "_load_approval", return_value=approval),
        patch.object(service._findings, "_get_owned_finding", return_value=finding),
        patch.object(service._findings, "_write_history"),
        patch.object(service._findings, "_load", return_value=finding),
    ):
        service.decide_approval(db, tenant, uuid.uuid4(), status="approved")

    assert finding.status == "accepted"
    assert finding.reviewed_by == tenant.user.id
    assert isinstance(finding.reviewed_at, datetime)
    assert finding.reviewed_at.tzinfo is not None


@patch("app.services.finding_lifecycle_service.assert_project_allows_mutation")
def test_partner_approval_writes_finding_status_history(mock_guard):
    from app.services.review_workflow_service import ReviewWorkflowService

    service = ReviewWorkflowService()
    finding_id = uuid.uuid4()
    finding = _finding(status="open")
    finding.id = finding_id
    tenant = _tenant(role="partner")
    approval = MagicMock()
    approval.engagement_id = uuid.uuid4()
    approval.finding_id = finding_id
    approval.comments = None
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [approval, finding]
    history_calls: list[dict] = []

    def _capture_history(*_args, **kwargs):
        history_calls.append(
            {
                "previous_status": kwargs["previous_status"],
                "new_status": kwargs["new_status"],
                "action": kwargs["action"],
                "changed_by": kwargs["changed_by"],
                "change_reason": kwargs.get("change_reason"),
            }
        )

    with (
        patch(
            "app.services.review_workflow_service.get_owned_engagement",
            return_value=MagicMock(),
        ),
        patch.object(service, "_load_approval", return_value=approval),
        patch.object(service._findings, "_get_owned_finding", return_value=finding),
        patch.object(service._findings, "_write_history", side_effect=_capture_history),
        patch.object(service._findings, "_load", return_value=finding),
    ):
        service.decide_approval(
            db, tenant, uuid.uuid4(), status="approved", comments="Partner sign-off"
        )

    assert len(history_calls) == 1
    assert history_calls[0]["action"] == "status_change"
    assert history_calls[0]["previous_status"] == "open"
    assert history_calls[0]["new_status"] == "accepted"
    assert history_calls[0]["changed_by"] == tenant.user.id
    assert history_calls[0]["change_reason"] == "Partner sign-off"
    assert finding.reviewed_by == tenant.user.id
    assert isinstance(finding.reviewed_at, datetime)
