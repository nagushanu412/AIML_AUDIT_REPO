"""Generic module engines."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import AuditModuleCatalog, AuditProject, ModuleAnalysisRun, Report
from app.services.evidence_gate import assert_project_findings_have_evidence
from app.services.module_framework.llm_provider import LLMRequest, get_llm_provider
from app.services.module_framework.protocol import (
    AnalysisPipelineResult,
    ModuleProvider,
    UploadResult,
)
from app.services.module_framework.registry import ModuleRegistry, get_module_registry
from app.services.project_access import get_owned_project
from app.services.run_lock_guard import assert_project_allows_mutation
from app.services.tenant_context import TenantContext


class UploadEngine:
    def upload(
        self,
        db: Session,
        tenant: TenantContext,
        project_id: uuid.UUID,
        content: bytes,
        provider: ModuleProvider,
    ) -> UploadResult:
        project = get_owned_project(db, project_id, tenant)
        provider.ensure_project_type(project)
        assert_project_allows_mutation(db, project.id)

        settings = get_settings()
        if len(content) > settings.max_upload_bytes:
            raise ValueError(
                f"File too large. Maximum size is {settings.max_upload_mb} MB."
            )

        validation, payload, extras = provider.validate_upload(content)
        if not validation.is_valid or payload is None:
            return UploadResult(
                project_id=project.id,
                validation=validation,
                records_imported=0,
                message="Validation failed. No records were saved.",
                extras=extras,
            )

        count = provider.save_upload(db, project, payload, extras)
        return UploadResult(
            project_id=project.id,
            validation=validation,
            records_imported=count,
            message=f"Successfully imported {count} records.",
            extras=extras,
        )


class ValidationEngine:
    def verify_project_data(
        self, db: Session, project_id: uuid.UUID, provider: ModuleProvider
    ) -> int:
        count = provider.count_records(db, project_id)
        if count < 1:
            raise ValueError(
                "No uploaded records found for this project. Upload data before analysis."
            )
        return count


class RuleEngineService:
    def run(
        self, db: Session, project_id: uuid.UUID, provider: ModuleProvider
    ):
        assert_project_allows_mutation(db, project_id)
        return provider.run_rules(db, project_id)


class RiskEngineService:
    def run(
        self, db: Session, project_id: uuid.UUID, provider: ModuleProvider
    ):
        assert_project_allows_mutation(db, project_id)
        # Remediation M2: block risk scoring when any finding lacks evidence_links
        assert_project_findings_have_evidence(db, project_id)
        return provider.run_risk(db, project_id)


class FindingsEngineService:
    def generate(
        self, db: Session, project_id: uuid.UUID, provider: ModuleProvider
    ) -> list:
        assert_project_allows_mutation(db, project_id)
        return provider.generate_findings(db, project_id)


class ReportEngineService:
    def generate(
        self,
        db: Session,
        project: AuditProject,
        user_id: uuid.UUID,
        provider: ModuleProvider,
        report_type: str | None = None,
    ) -> Report:
        assert_project_allows_mutation(db, project.id)
        return provider.generate_report(db, project, user_id, report_type)


PIPELINE_STEPS = (
    "validation",
    "rules",
    "risk",
    "findings",
    "ai_narrative",
    "report",
    "completion",
)


class AnalysisEngine:
    """Orchestrates the audit pipeline for analysis runs."""

    def __init__(
        self,
        registry: ModuleRegistry | None = None,
        validation_engine: ValidationEngine | None = None,
        rule_engine: RuleEngineService | None = None,
        risk_engine: RiskEngineService | None = None,
        findings_engine: FindingsEngineService | None = None,
        report_engine: ReportEngineService | None = None,
    ) -> None:
        self._registry = registry or get_module_registry()
        self._validation = validation_engine or ValidationEngine()
        self._rules = rule_engine or RuleEngineService()
        self._risk = risk_engine or RiskEngineService()
        self._findings = findings_engine or FindingsEngineService()
        self._reports = report_engine or ReportEngineService()
        self._llm = get_llm_provider()

    def _update_progress(
        self,
        db: Session,
        run: ModuleAnalysisRun,
        *,
        pct: int,
        message: str,
        step: str,
    ) -> None:
        run.progress_pct = pct
        run.progress_message = message
        run.pipeline_step = step
        db.commit()

    def execute_run(self, db: Session, run_id: uuid.UUID) -> AnalysisPipelineResult:
        run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
        if not run:
            raise ValueError(f"Analysis run '{run_id}' not found.")
        if not run.project_id:
            raise ValueError("Analysis run has no linked project.")

        module = (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.id == run.module_catalog_id)
            .first()
            if run.module_catalog_id
            else None
        )
        if not module:
            raise ValueError("Analysis run has no linked module.")

        provider = self._registry.resolve_provider(db, module.code)
        project = db.query(AuditProject).filter(AuditProject.id == run.project_id).first()
        if not project:
            raise ValueError("Linked project not found.")

        provider.ensure_project_type(project)
        steps_completed: list[str] = []
        report_id: uuid.UUID | None = None

        try:
            self._update_progress(
                db,
                run,
                pct=10,
                message="Verifying uploaded data",
                step="validation",
            )
            self._validation.verify_project_data(db, project.id, provider)
            steps_completed.append("validation")

            self._update_progress(
                db, run, pct=30, message="Running rule engine", step="rules"
            )
            self._rules.run(db, project.id, provider)
            steps_completed.append("rules")

            self._update_progress(
                db, run, pct=50, message="Running risk engine", step="risk"
            )
            self._risk.run(db, project.id, provider)
            steps_completed.append("risk")

            self._update_progress(
                db, run, pct=70, message="Generating findings", step="findings"
            )
            findings = self._findings.generate(db, project.id, provider)
            steps_completed.append("findings")

            self._update_progress(
                db,
                run,
                pct=80,
                message="AI narrative (skipped — M4)",
                step="ai_narrative",
            )
            self._llm.complete(LLMRequest(prompt="", context={"run_id": str(run.id)}))
            steps_completed.append("ai_narrative")

            self._update_progress(
                db, run, pct=90, message="Generating report", step="report"
            )
            report = self._reports.generate(
                db,
                project,
                run.run_owner_id or project.id,
                provider,
            )
            report_id = report.id
            steps_completed.append("report")

            run.status = "completed"
            run.progress_pct = 100
            run.progress_message = "Analysis completed"
            run.pipeline_step = "completion"
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = None
            run.error_detail = None
            db.commit()
            steps_completed.append("completion")

            return AnalysisPipelineResult(
                run_id=run.id,
                project_id=project.id,
                module_code=module.code,
                steps_completed=steps_completed,
                findings_count=len(findings),
                report_id=report_id,
            )
        except Exception as exc:
            db.rollback()
            run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
            if run:
                run.status = "draft"
                run.error_message = str(exc)
                run.error_detail = {"steps_completed": steps_completed, "failed_at": run.pipeline_step}
                run.progress_message = "Analysis failed"
                db.commit()
            raise
