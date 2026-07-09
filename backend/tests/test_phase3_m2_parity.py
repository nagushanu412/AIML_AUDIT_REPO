"""Phase 3 M2 — Legacy vs generic framework parity tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.excel_validator import validate_excel
from app.services.module_framework.legacy_adapter import MODULE_CODES, legacy_adapter
from app.services.module_framework.plugins import PLUGIN_BUILDERS
from app.services.module_framework.protocol import ModuleMetadata
from app.services.module_framework.registry import ModuleRegistry
from app.services.procurement_validator import validate_procurement_excel
from app.services.revenue_validator import validate_revenue_excel

SAMPLES = Path(__file__).resolve().parents[2] / "database"


def _meta(code: str, **kwargs) -> ModuleMetadata:
    defaults = {
        "JOURNAL_ENTRY_TESTING": dict(
            name="Journal Entry Testing",
            project_type="journal_testing",
            slug="journal-entry-testing",
            category="General Ledger",
            icon="BookOpen",
            implementation_status="built",
        ),
        "REVENUE_TESTING": dict(
            name="Revenue Testing",
            project_type="revenue_testing",
            slug="revenue-testing",
            category="Revenue",
            icon="Receipt",
            implementation_status="built",
        ),
        "PROCUREMENT_TESTING": dict(
            name="Procurement Testing",
            project_type="procurement_testing",
            slug="procurement-testing",
            category="Procurement",
            icon="ShoppingCart",
            implementation_status="built",
        ),
    }
    base = defaults[code]
    base.update(kwargs)
    return ModuleMetadata(code=code, **base)


@pytest.mark.parametrize(
    "code",
    ["JOURNAL_ENTRY_TESTING", "REVENUE_TESTING", "PROCUREMENT_TESTING"],
)
def test_plugin_builders_match_module_codes(code: str):
    assert code in PLUGIN_BUILDERS
    assert MODULE_CODES["journal" if "JOURNAL" in code else "revenue" if "REVENUE" in code else "procurement"] == code


def test_journal_validator_plugin_matches_direct_service():
    sample = SAMPLES / "sample_journal_entries.xlsx"
    if not sample.is_file():
        pytest.skip("sample_journal_entries.xlsx not found")
    content = sample.read_bytes()
    direct_validation, direct_df = validate_excel(content)
    plugin = PLUGIN_BUILDERS["JOURNAL_ENTRY_TESTING"](_meta("JOURNAL_ENTRY_TESTING"))
    plugin_validation, plugin_df, _ = plugin.validate_upload(content)
    assert direct_validation.is_valid == plugin_validation.is_valid
    assert direct_validation.total_rows == plugin_validation.total_rows
    if direct_df is not None and plugin_df is not None:
        assert len(direct_df) == len(plugin_df)


def test_revenue_validator_plugin_matches_direct_service():
    sample = SAMPLES / "sample_revenue_invoices.xlsx"
    if not sample.is_file():
        pytest.skip("sample_revenue_invoices.xlsx not found")
    content = sample.read_bytes()
    direct_validation, direct_df, t1, g1, r1 = validate_revenue_excel(content)
    plugin = PLUGIN_BUILDERS["REVENUE_TESTING"](_meta("REVENUE_TESTING"))
    plugin_validation, plugin_df, extras = plugin.validate_upload(content)
    assert direct_validation.is_valid == plugin_validation.is_valid
    assert extras.get("total_taxable") == t1
    assert extras.get("total_gst") == g1
    assert extras.get("total_revenue") == r1
    if direct_df is not None and plugin_df is not None:
        assert len(direct_df) == len(plugin_df)


def test_procurement_validator_plugin_matches_direct_service():
    sample = SAMPLES / "sample_procurement_invoices.xlsx"
    if not sample.is_file():
        pytest.skip("sample_procurement_invoices.xlsx not found")
    content = sample.read_bytes()
    direct_validation, direct_df, t1, g1, s1 = validate_procurement_excel(content)
    plugin = PLUGIN_BUILDERS["PROCUREMENT_TESTING"](_meta("PROCUREMENT_TESTING"))
    plugin_validation, plugin_df, extras = plugin.validate_upload(content)
    assert direct_validation.is_valid == plugin_validation.is_valid
    assert extras.get("total_taxable") == t1
    assert extras.get("total_gst") == g1
    assert extras.get("total_amount") == s1
    if direct_df is not None and plugin_df is not None:
        assert len(direct_df) == len(plugin_df)


def test_legacy_adapter_exposes_three_module_codes():
    assert set(MODULE_CODES.values()) == {
        "JOURNAL_ENTRY_TESTING",
        "REVENUE_TESTING",
        "PROCUREMENT_TESTING",
    }


def test_registry_static_plugin_matches_builder():
    registry = ModuleRegistry()
    for code in PLUGIN_BUILDERS:
        meta = _meta(code)
        built = PLUGIN_BUILDERS[code](meta)
        registry.register_static(built)
        assert registry._static_providers[code].code == code


def test_journal_plugin_default_report_unchanged():
    plugin = PLUGIN_BUILDERS["JOURNAL_ENTRY_TESTING"](_meta("JOURNAL_ENTRY_TESTING"))
    assert plugin.default_report_type() == "journal_audit_summary"


def test_revenue_plugin_default_report_unchanged():
    plugin = PLUGIN_BUILDERS["REVENUE_TESTING"](_meta("REVENUE_TESTING"))
    assert plugin.default_report_type() == "revenue_audit_excel"


def test_procurement_plugin_default_report_unchanged():
    plugin = PLUGIN_BUILDERS["PROCUREMENT_TESTING"](_meta("PROCUREMENT_TESTING"))
    assert plugin.default_report_type() == "procurement_audit_excel"


def test_legacy_adapter_singleton():
    assert legacy_adapter is not None
    assert hasattr(legacy_adapter, "journal_upload")
    assert hasattr(legacy_adapter, "run_rules")
