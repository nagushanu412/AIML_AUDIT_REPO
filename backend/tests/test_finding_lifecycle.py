"""Unit tests for Phase 2 Milestone 3 — Finding Lifecycle."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.services.finding_lifecycle_constants import (
    FINDING_STATUSES,
    STATUS_TRANSITIONS,
)
from app.services.finding_lifecycle_service import FindingLifecycleService


def test_finding_statuses_include_five_states():
    assert len(FINDING_STATUSES) == 5
    assert "under_review" in FINDING_STATUSES
    assert "cleared" in FINDING_STATUSES


def test_open_can_transition_to_under_review():
    assert "under_review" in STATUS_TRANSITIONS["open"]


def test_closed_can_reopen_to_open():
    assert "open" in STATUS_TRANSITIONS["closed"]


def test_invalid_status_rejected():
    service = FindingLifecycleService()
    with pytest.raises(ValueError, match="Invalid status"):
        service._validate_status("invalid")


def test_approve_requires_elevated_role():
    service = FindingLifecycleService()
    tenant = MagicMock()
    tenant.member_role = "auditor"
    with pytest.raises(PermissionError, match="permission"):
        service._assert_can_approve(tenant)


def test_resolve_module_labels_from_project_type():
    service = FindingLifecycleService()
    name, code = service._resolve_module_labels("revenue_testing", "REV_CUTOFF")
    assert name == "Revenue Testing"
    assert code == "REVENUE_TESTING"


def test_resolve_module_labels_from_rule_code_prefix():
    service = FindingLifecycleService()
    name, code = service._resolve_module_labels(None, "PROC_DUPLICATE_PAYMENT")
    assert name == "Procurement Testing"
    assert code == "PROCUREMENT_TESTING"


def test_resolve_module_labels_defaults_to_journal():
    service = FindingLifecycleService()
    name, code = service._resolve_module_labels(None, "LARGE_VALUE")
    assert name == "Journal Entry Testing"
    assert code == "JOURNAL_ENTRY_TESTING"
