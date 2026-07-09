"""Journal Entry Testing module plugin."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, AuditProject, JournalEntry, Report
from app.schemas.upload import ValidationResult
from app.services.excel_validator import validate_excel
from app.services.findings_service import generate_findings
from app.services.module_framework.plugins.base import BaseModuleProvider
from app.services.module_framework.protocol import (
    ModuleMetadata,
    RunRiskResult,
    RunRulesResult,
)
from app.services.report_service import generate_project_report
from app.services.risk_scoring import get_risk_scores, run_risk_scoring
from app.services.rule_runner import run_rules_for_project
from app.services.upload_service import save_journal_entries


class JournalEntryPlugin(BaseModuleProvider):
    code = "JOURNAL_ENTRY_TESTING"
    project_type = "journal_testing"

    def validate_upload(self, content: bytes) -> tuple[ValidationResult, object, dict]:
        validation, df = validate_excel(content)
        return validation, df, {}

    def save_upload(
        self, db: Session, project: AuditProject, payload: object, extras: dict
    ) -> int:
        del extras
        return save_journal_entries(db, project, payload)

    def count_records(self, db: Session, project_id: uuid.UUID) -> int:
        return (
            db.query(JournalEntry).filter(JournalEntry.project_id == project_id).count()
        )

    def run_rules(self, db: Session, project_id: uuid.UUID) -> RunRulesResult:
        result = run_rules_for_project(db, project_id)
        violations_by_rule = result.get("violations_by_rule", {})
        return RunRulesResult(
            project_id=project_id,
            total_rules_run=len(result.get("rule_summary", [])),
            total_violations=result.get("total_violations_found", 0),
            rule_summary=violations_by_rule,
            message=result.get("message", "Rules executed."),
            legacy_payload=result,
        )

    def run_risk(self, db: Session, project_id: uuid.UUID) -> RunRiskResult:
        result = run_risk_scoring(db, project_id)
        return RunRiskResult(
            project_id=project_id,
            total_scored=result.get("total_entries_scored", 0),
            high_risk=result.get("high_risk", 0),
            medium_risk=result.get("medium_risk", 0),
            low_risk=result.get("low_risk", 0),
            message=result.get("message", "Risk scoring completed."),
            legacy_payload=result,
        )

    def generate_findings(self, db: Session, project_id: uuid.UUID) -> list:
        return generate_findings(db, project_id)

    def list_risk_scores(
        self,
        db: Session,
        project_id: uuid.UUID,
        *,
        risk_category: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        return get_risk_scores(
            db, project_id, risk_category=risk_category, limit=limit, offset=offset
        )

    def list_findings(self, db: Session, project_id: uuid.UUID) -> list:
        return (
            db.query(AuditFinding)
            .filter(AuditFinding.project_id == project_id)
            .order_by(AuditFinding.created_at.desc())
            .all()
        )

    def default_report_type(self) -> str:
        return "journal_audit_summary"

    def generate_report(
        self,
        db: Session,
        project: AuditProject,
        user_id: uuid.UUID,
        report_type: str | None = None,
    ) -> Report:
        return generate_project_report(
            db, project, user_id, report_type or self.default_report_type()
        )


def build_journal_entry_plugin(metadata: ModuleMetadata) -> JournalEntryPlugin:
    return JournalEntryPlugin(metadata)
