"""Phase 3 M1 — Generic Module Framework tests."""

from __future__ import annotations

import uuid

import pytest

from app.services.module_framework.engines import (
    AnalysisEngine,
    FindingsEngineService,
    ReportEngineService,
    RiskEngineService,
    RuleEngineService,
    UploadEngine,
    ValidationEngine,
)
from app.services.module_framework.llm_provider import LLMRequest, NoOpLLMProvider, get_llm_provider
from app.services.module_framework.plugin_config_seed import PLUGIN_CONFIG_SEED
from app.services.module_framework.plugins import PLUGIN_BUILDERS
from app.services.module_framework.protocol import ModuleMetadata
from app.services.module_framework.registry import ModuleRegistry


def test_plugin_config_seed_has_three_modules():
    codes = {row["module_code"] for row in PLUGIN_CONFIG_SEED}
    assert codes == {
        "JOURNAL_ENTRY_TESTING",
        "REVENUE_TESTING",
        "PROCUREMENT_TESTING",
    }


def test_plugin_builders_registered():
    assert set(PLUGIN_BUILDERS.keys()) == {
        "JOURNAL_ENTRY_TESTING",
        "REVENUE_TESTING",
        "PROCUREMENT_TESTING",
    }


def test_build_journal_plugin_metadata():
    builder = PLUGIN_BUILDERS["JOURNAL_ENTRY_TESTING"]
    meta = ModuleMetadata(
        code="JOURNAL_ENTRY_TESTING",
        name="Journal Entry Testing",
        project_type="journal_testing",
        slug="journal-entry-testing",
        category="General Ledger",
        icon="BookOpen",
        implementation_status="built",
    )
    plugin = builder(meta)
    assert plugin.code == "JOURNAL_ENTRY_TESTING"
    assert plugin.project_type == "journal_testing"
    assert plugin.default_report_type() == "journal_audit_summary"


def test_build_revenue_plugin_metadata():
    builder = PLUGIN_BUILDERS["REVENUE_TESTING"]
    meta = ModuleMetadata(
        code="REVENUE_TESTING",
        name="Revenue Testing",
        project_type="revenue_testing",
        slug="revenue-testing",
        category="Revenue",
        icon="Receipt",
        implementation_status="built",
    )
    plugin = builder(meta)
    assert plugin.default_report_type() == "revenue_audit_excel"


def test_build_procurement_plugin_metadata():
    builder = PLUGIN_BUILDERS["PROCUREMENT_TESTING"]
    meta = ModuleMetadata(
        code="PROCUREMENT_TESTING",
        name="Procurement Testing",
        project_type="procurement_testing",
        slug="procurement-testing",
        category="Procurement",
        icon="ShoppingCart",
        implementation_status="built",
    )
    plugin = builder(meta)
    assert plugin.default_report_type() == "procurement_audit_excel"


def test_noop_llm_provider():
    provider = get_llm_provider()
    assert isinstance(provider, NoOpLLMProvider)
    response = provider.complete(LLMRequest(prompt="test"))
    assert response.provider == "noop"
    assert response.content == ""


def test_module_registry_static_register():
    registry = ModuleRegistry()
    meta = ModuleMetadata(
        code="JOURNAL_ENTRY_TESTING",
        name="Journal Entry Testing",
        project_type="journal_testing",
        slug="journal-entry-testing",
        category="General Ledger",
        icon="BookOpen",
        implementation_status="built",
    )
    plugin = PLUGIN_BUILDERS["JOURNAL_ENTRY_TESTING"](meta)
    registry.register_static(plugin)
    assert registry._static_providers["JOURNAL_ENTRY_TESTING"] is plugin


def test_validation_engine_requires_records():
    class FakeProvider:
        def count_records(self, db, project_id):
            return 0

    engine = ValidationEngine()
    with pytest.raises(ValueError, match="No uploaded records"):
        engine.verify_project_data(None, uuid.uuid4(), FakeProvider())


def test_analysis_engine_has_pipeline_dependencies():
    engine = AnalysisEngine()
    assert engine._validation is not None
    assert engine._rules is not None
    assert engine._risk is not None
    assert engine._findings is not None
    assert engine._reports is not None


def test_generic_engines_instantiate():
    assert UploadEngine() is not None
    assert RuleEngineService() is not None
    assert RiskEngineService() is not None
    assert FindingsEngineService() is not None
    assert ReportEngineService() is not None
