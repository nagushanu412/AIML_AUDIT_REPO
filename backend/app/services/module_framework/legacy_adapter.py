"""Legacy route adapter — delegates to generic engines with legacy response shapes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import AuditEngagement, AuditFinding, AuditProject, Client, Report
from app.schemas.procurement import (
    ProcurementRiskScoreOut,
    ProcurementRunRiskResponse,
    ProcurementRunRulesResponse,
    ProcurementUploadResponse,
)
from app.schemas.revenue import (
    RevenueRiskScoreOut,
    RevenueRunRiskResponse,
    RevenueRunRulesResponse,
    RevenueUploadResponse,
)
from app.schemas.upload import UploadResponse
from app.services.module_framework.engines import (
    FindingsEngineService,
    ReportEngineService,
    RiskEngineService,
    RuleEngineService,
    UploadEngine,
)
from app.services.module_framework.protocol import UploadResult
from app.services.module_framework.registry import get_module_registry
from app.services.project_access import client_list_filter, get_owned_project
from app.services.rule_runner import get_rule_results
from app.services.tenant_context import TenantContext

MODULE_CODES = {
    "journal": "JOURNAL_ENTRY_TESTING",
    "revenue": "REVENUE_TESTING",
    "procurement": "PROCUREMENT_TESTING",
}

DEPRECATION_HEADERS = {
    "Deprecation": "true",
    "Sunset": "2026-12-31",
    "Link": '</modules/{code}/>; rel="successor-version"',
}


class LegacyModuleAdapter:
    def __init__(self) -> None:
        self._registry = get_module_registry()
        self._upload = UploadEngine()
        self._rules = RuleEngineService()
        self._risk = RiskEngineService()
        self._findings = FindingsEngineService()
        self._reports = ReportEngineService()

    def _provider(self, db: Session, module_code: str):
        return self._registry.resolve_provider(db, module_code)

    def _project(
        self, db: Session, project_id: uuid.UUID, tenant: TenantContext
    ) -> AuditProject:
        return get_owned_project(db, project_id, tenant)

    @staticmethod
    def validate_xlsx(filename: str | None) -> None:
        if not filename or not filename.lower().endswith(".xlsx"):
            raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    @staticmethod
    def validate_size(content: bytes) -> None:
        settings = get_settings()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_upload_mb} MB.",
            )

    def journal_upload(
        self,
        db: Session,
        tenant: TenantContext,
        project_id: uuid.UUID,
        content: bytes,
    ) -> UploadResponse:
        provider = self._provider(db, MODULE_CODES["journal"])
        result = self._upload.upload(db, tenant, project_id, content, provider)
        return UploadResponse(
            project_id=result.project_id,
            validation=result.validation,
            entries_imported=result.records_imported,
            message=(
                f"Successfully imported {result.records_imported} journal entries."
                if result.records_imported
                else "Validation failed. No records were saved."
            ),
        )

    def invoice_upload(
        self,
        db: Session,
        tenant: TenantContext,
        module_key: str,
        project_id: uuid.UUID,
        content: bytes,
    ) -> RevenueUploadResponse | ProcurementUploadResponse:
        module_code = MODULE_CODES[module_key]
        provider = self._provider(db, module_code)
        result = self._upload.upload(db, tenant, project_id, content, provider)
        if not result.validation.is_valid or result.records_imported == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": f"{module_key.title()} file validation failed.",
                    "validation": result.validation.model_dump(),
                },
            )
        extras = result.extras
        if module_key == "revenue":
            return RevenueUploadResponse(
                project_id=result.project_id,
                validation=result.validation,
                invoices_imported=result.records_imported,
                total_taxable=extras.get("total_taxable", 0),
                total_gst=extras.get("total_gst", 0),
                total_revenue=extras.get("total_revenue", 0),
                message=f"Imported {result.records_imported} revenue invoices successfully.",
            )
        return ProcurementUploadResponse(
            project_id=result.project_id,
            validation=result.validation,
            invoices_imported=result.records_imported,
            total_taxable=extras.get("total_taxable", 0),
            total_gst=extras.get("total_gst", 0),
            total_spend=extras.get("total_amount", 0),
            message=f"Imported {result.records_imported} vendor invoices successfully.",
        )

    def run_rules(
        self, db: Session, tenant: TenantContext, module_code: str, project_id: uuid.UUID
    ) -> dict:
        project = self._project(db, project_id, tenant)
        provider = self._provider(db, module_code)
        provider.ensure_project_type(project)
        result = self._rules.run(db, project_id, provider)
        return result.legacy_payload

    def run_risk(
        self, db: Session, tenant: TenantContext, module_code: str, project_id: uuid.UUID
    ) -> dict:
        project = self._project(db, project_id, tenant)
        provider = self._provider(db, module_code)
        provider.ensure_project_type(project)
        result = self._risk.run(db, project_id, provider)
        return result.legacy_payload

    def list_risk_scores(
        self,
        db: Session,
        tenant: TenantContext,
        module_code: str,
        project_id: uuid.UUID,
        *,
        risk_category: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        project = self._project(db, project_id, tenant)
        provider = self._provider(db, module_code)
        provider.ensure_project_type(project)
        return provider.list_risk_scores(
            db, project_id, risk_category=risk_category, limit=limit, offset=offset
        )

    def generate_findings(
        self, db: Session, tenant: TenantContext, module_code: str, project_id: uuid.UUID
    ) -> list:
        project = self._project(db, project_id, tenant)
        provider = self._provider(db, module_code)
        provider.ensure_project_type(project)
        return self._findings.generate(db, project_id, provider)

    def list_findings(
        self, db: Session, tenant: TenantContext, module_code: str, project_id: uuid.UUID
    ) -> list:
        project = self._project(db, project_id, tenant)
        provider = self._provider(db, module_code)
        provider.ensure_project_type(project)
        return provider.list_findings(db, project_id)

    def generate_report(
        self,
        db: Session,
        tenant: TenantContext,
        project_id: uuid.UUID,
        report_type: str,
    ) -> Report:
        project = self._project(db, project_id, tenant)
        module_code = {
            "journal_testing": MODULE_CODES["journal"],
            "revenue_testing": MODULE_CODES["revenue"],
            "procurement_testing": MODULE_CODES["procurement"],
        }.get(project.project_type, MODULE_CODES["journal"])
        provider = self._provider(db, module_code)
        return self._reports.generate(db, project, tenant.user.id, provider, report_type)

    def list_reports(
        self,
        db: Session,
        tenant: TenantContext,
        project_id: uuid.UUID | None = None,
    ) -> list[Report]:
        query = (
            db.query(Report)
            .join(AuditProject)
            .join(AuditEngagement)
            .join(Client)
            .filter(client_list_filter(tenant))
        )
        if project_id:
            self._project(db, project_id, tenant)
            query = query.filter(Report.project_id == project_id)
        return query.order_by(Report.created_at.desc()).limit(100).all()

    @staticmethod
    def map_revenue_risk_scores(rows: list[dict]) -> list[RevenueRiskScoreOut]:
        return [
            RevenueRiskScoreOut(
                **row,
                invoice_date=row["invoice_date"].isoformat() if row.get("invoice_date") else None,
                total_amount=float(row["total_amount"]),
                gst_amount=float(row["gst_amount"]),
            )
            for row in rows
        ]

    @staticmethod
    def map_procurement_risk_scores(rows: list[dict]) -> list[ProcurementRiskScoreOut]:
        return [
            ProcurementRiskScoreOut(
                **row,
                invoice_date=row["invoice_date"].isoformat() if row.get("invoice_date") else None,
                total_amount=float(row["total_amount"]),
                gst_amount=float(row["gst_amount"]),
            )
            for row in rows
        ]

    def journal_rule_results(
        self,
        db: Session,
        tenant: TenantContext,
        project_id: uuid.UUID,
        *,
        rule_code: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        self._project(db, project_id, tenant)
        return get_rule_results(
            db, project_id, rule_code=rule_code, limit=limit, offset=offset
        )


legacy_adapter = LegacyModuleAdapter()
