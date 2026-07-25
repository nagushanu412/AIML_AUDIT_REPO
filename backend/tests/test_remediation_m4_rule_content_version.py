"""Remediation Milestone 4 Step 3 — rule_content_version on rules and findings."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import inspect, text

from app.database import SessionLocal, validate_database_connection
from app.models.audit import AuditFinding, RuleMaster
from app.services.findings_service import generate_findings
from app.services.procurement_findings_service import generate_procurement_findings
from app.services.revenue_findings_service import generate_revenue_findings


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def test_rule_master_model_has_rule_content_version():
    assert hasattr(RuleMaster, "rule_content_version")
    assert hasattr(AuditFinding, "rule_content_version")


@requires_db
def test_db_columns_exist_with_expected_nullability():
    db = SessionLocal()
    try:
        rules_cols = {c["name"]: c for c in inspect(db.bind).get_columns("rules_master")}
        finding_cols = {c["name"]: c for c in inspect(db.bind).get_columns("audit_findings")}
        assert "rule_content_version" in rules_cols
        assert rules_cols["rule_content_version"]["nullable"] is False
        assert "rule_content_version" in finding_cols
        assert finding_cols["rule_content_version"]["nullable"] is True

        min_ver = db.execute(
            text("SELECT MIN(rule_content_version) FROM rules_master")
        ).scalar()
        if min_ver is not None:
            assert int(min_ver) >= 1
    finally:
        db.close()


def _query_side_effect(*, rule_model, result_model, rule, violation):
    def _side_effect(model):
        if model is AuditFinding:
            q = MagicMock()
            q.filter.return_value.delete.return_value = 0
            return q
        if model is rule_model:
            q = MagicMock()
            q.all.return_value = [rule]
            return q
        if model is result_model:
            q = MagicMock()
            q.filter.return_value.all.return_value = [violation]
            return q
        return MagicMock()

    return _side_effect


def test_generate_findings_snapshots_rule_content_version():
    from app.models.audit import RuleResult

    rule = MagicMock()
    rule.rule_code = "LARGE_VALUE"
    rule.default_score = 20
    rule.rule_content_version = 3

    violation = MagicMock()
    violation.rule_code = "LARGE_VALUE"
    violation.journal_entry_id = uuid.uuid4()

    db = MagicMock()
    db.query.side_effect = _query_side_effect(
        rule_model=RuleMaster, result_model=RuleResult, rule=rule, violation=violation
    )

    with patch("app.services.findings_service.FINDING_TEMPLATES", {"LARGE_VALUE": {}}):
        findings = generate_findings(db, uuid.uuid4())

    assert len(findings) == 1
    assert findings[0].rule_content_version == 3
    db.add_all.assert_called_once()
    db.commit.assert_called_once()


def test_generate_revenue_findings_snapshots_rule_content_version():
    from app.models.audit import RevenueRuleResult

    rule = MagicMock()
    rule.rule_code = "REV_CUTOFF"
    rule.default_score = 15
    rule.rule_content_version = 2

    violation = MagicMock()
    violation.rule_code = "REV_CUTOFF"
    violation.revenue_invoice_id = uuid.uuid4()

    db = MagicMock()
    db.query.side_effect = _query_side_effect(
        rule_model=RuleMaster,
        result_model=RevenueRuleResult,
        rule=rule,
        violation=violation,
    )

    with patch(
        "app.services.revenue_findings_service.REVENUE_FINDING_TEMPLATES",
        {"REV_CUTOFF": {}},
    ):
        findings = generate_revenue_findings(db, uuid.uuid4())

    assert len(findings) == 1
    assert findings[0].rule_content_version == 2


def test_generate_procurement_findings_snapshots_rule_content_version():
    from app.models.audit import ProcurementRuleResult

    rule = MagicMock()
    rule.rule_code = "PROC_DUPLICATE_PAYMENT"
    rule.default_score = 15
    rule.rule_content_version = 4

    violation = MagicMock()
    violation.rule_code = "PROC_DUPLICATE_PAYMENT"
    violation.procurement_invoice_id = uuid.uuid4()

    db = MagicMock()
    db.query.side_effect = _query_side_effect(
        rule_model=RuleMaster,
        result_model=ProcurementRuleResult,
        rule=rule,
        violation=violation,
    )

    with patch(
        "app.services.procurement_findings_service.PROCUREMENT_FINDING_TEMPLATES",
        {"PROC_DUPLICATE_PAYMENT": {}},
    ):
        findings = generate_procurement_findings(db, uuid.uuid4())

    assert len(findings) == 1
    assert findings[0].rule_content_version == 4


def test_update_rule_bumps_rule_content_version():
    from app.routers import rules_master as rules_router
    from app.schemas.rules_master import RuleMasterUpdate

    rule = MagicMock()
    rule.id = uuid.uuid4()
    rule.rule_code = "LARGE_VALUE"
    rule.rule_name = "Large Value"
    rule.description = "old"
    rule.default_score = 10
    rule.is_active = True
    rule.config_schema = {"threshold": 1000}
    rule.rule_content_version = 1

    db = MagicMock()
    body = RuleMasterUpdate(description="new methodology text")

    with patch.object(rules_router, "_get_rule_or_404", return_value=rule):
        result = rules_router.update_rule(rule.id, body, db=db, current_user=MagicMock())

    assert result is rule
    assert rule.description == "new methodology text"
    assert rule.rule_content_version == 2
    db.commit.assert_called_once()


def test_bump_then_generate_leaves_prior_finding_stamp_unchanged():
    """Prior finding keeps stamped version; new generation uses bumped version.

    Note: generate_findings deletes findings for its project_id only — a finding
    on another project (or an already-materialized prior row) must not be rewritten.
    """
    from app.models.audit import RuleResult
    from app.routers import rules_master as rules_router
    from app.schemas.rules_master import RuleMasterUpdate

    prior_finding = AuditFinding(
        project_id=uuid.uuid4(),
        rule_code="LARGE_VALUE",
        finding_title="Prior LARGE_VALUE",
        observation="Generated under version 1",
        risk_level="medium",
        impact="impact",
        recommendation="recommendation",
        affected_count=1,
        source_record_ids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        rule_content_version=1,
    )

    rule = MagicMock()
    rule.id = uuid.uuid4()
    rule.rule_code = "LARGE_VALUE"
    rule.rule_name = "Large Value"
    rule.description = "v1 text"
    rule.default_score = 20
    rule.is_active = True
    rule.config_schema = {"threshold": 1000}
    rule.rule_content_version = 1

    bump_db = MagicMock()
    with patch.object(rules_router, "_get_rule_or_404", return_value=rule):
        rules_router.update_rule(
            rule.id,
            RuleMasterUpdate(description="v2 methodology"),
            db=bump_db,
            current_user=MagicMock(),
        )
    assert rule.rule_content_version == 2

    violation = MagicMock()
    violation.rule_code = "LARGE_VALUE"
    violation.journal_entry_id = uuid.uuid4()

    gen_db = MagicMock()
    gen_db.query.side_effect = _query_side_effect(
        rule_model=RuleMaster, result_model=RuleResult, rule=rule, violation=violation
    )
    with patch("app.services.findings_service.FINDING_TEMPLATES", {"LARGE_VALUE": {}}):
        new_findings = generate_findings(gen_db, uuid.uuid4())

    assert prior_finding.rule_content_version == 1
    assert len(new_findings) == 1
    assert new_findings[0].rule_content_version == 2
    assert new_findings[0].project_id != prior_finding.project_id
