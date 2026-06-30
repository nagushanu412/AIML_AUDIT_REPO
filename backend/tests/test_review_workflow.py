"""Unit tests for Phase 2 Milestone 4 — Review Workflow."""

from app.services.review_workflow_service import PARTNER_APPROVE_ROLES, REVIEWER_ROLES


def test_reviewer_roles_include_reviewer():
    assert "reviewer" in REVIEWER_ROLES


def test_partner_can_approve():
    assert "partner" in PARTNER_APPROVE_ROLES
