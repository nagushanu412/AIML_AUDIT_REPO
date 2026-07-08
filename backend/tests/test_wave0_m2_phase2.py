"""Wave 0 Milestone 2 — Phase 2 enterprise workflow unit tests."""

from unittest.mock import MagicMock

import pytest

from app.services.analysis_run_service import AnalysisRunService, RUN_STATUSES
from app.services.finding_relationship_service import RELATIONSHIP_TYPES
from app.services.module_catalog_constants import MODULE_CODE_TO_PROJECT_TYPE
from app.services.run_lock_guard import assert_project_allows_mutation, assert_run_allows_mutation


def test_run_statuses_include_phase2_lifecycle():
    assert "under_review" in RUN_STATUSES
    assert "locked" in RUN_STATUSES
    assert "archived" in RUN_STATUSES


def test_analysis_run_locked_is_immutable():
    run = MagicMock()
    run.status = "locked"
    with pytest.raises(ValueError, match="locked or archived"):
        AnalysisRunService.assert_run_mutable(run)


def test_analysis_run_archived_is_immutable():
    run = MagicMock()
    run.status = "archived"
    with pytest.raises(ValueError, match="locked or archived"):
        AnalysisRunService.assert_run_mutable(run)


def test_relationship_types_match_phase2_guide():
    assert "duplicate_of" in RELATIONSHIP_TYPES
    assert "root_cause" in RELATIONSHIP_TYPES
    assert "contradicts" in RELATIONSHIP_TYPES


def test_module_code_maps_to_project_type_for_auto_workspace():
    assert MODULE_CODE_TO_PROJECT_TYPE["JOURNAL_ENTRY_TESTING"] == "journal_testing"
    assert MODULE_CODE_TO_PROJECT_TYPE["REVENUE_TESTING"] == "revenue_testing"


def test_assert_run_allows_mutation_skips_none():
    assert_run_allows_mutation(MagicMock(), None)


def test_assert_project_allows_mutation_skips_none():
    assert_project_allows_mutation(MagicMock(), None)
