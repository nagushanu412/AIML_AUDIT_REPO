"""Unit tests for audit module catalog."""

from app.services.module_catalog_constants import (
    MODULE_CATALOG_SEED,
    PROJECT_TYPE_TO_MODULE_CODE,
)


def test_catalog_seed_has_22_modules():
    assert len(MODULE_CATALOG_SEED) == 22


def test_built_modules_in_seed():
    codes = {m["code"] for m in MODULE_CATALOG_SEED if m["implementation_status"] == "built"}
    assert codes == {"JOURNAL_ENTRY_TESTING", "REVENUE_TESTING", "PROCUREMENT_TESTING"}


def test_project_type_mapping():
    assert PROJECT_TYPE_TO_MODULE_CODE["journal_testing"] == "JOURNAL_ENTRY_TESTING"
