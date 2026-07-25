"""Generic module REST API — /modules/{module_code}/* per ADR-005."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditEngagement, AuditProject, Client, Report
from app.routers.errors import handle_service_error
from app.schemas.analytics import FindingOut, ReportOut
from app.services.evidence_gate import EvidenceGateViolation
from app.schemas.generic_modules import (
    GenericFindingsResponse,
    GenericReportGenerateResponse,
    GenericReportsResponse,
    GenericRunRiskResponse,
    GenericRunRulesResponse,
    GenericUploadResponse,
    ModuleMetadataOut,
    ModuleWorkspaceConfigOut,
)
from app.services.module_framework.engines import (
    FindingsEngineService,
    ReportEngineService,
    RiskEngineService,
    RuleEngineService,
    UploadEngine,
)
from app.services.module_framework.registry import (
    ModuleNotBuiltError,
    ModuleNotFoundError,
    get_module_registry,
)
from app.services.project_access import client_list_filter, get_owned_project
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/modules", tags=["Generic Modules"])

_registry = get_module_registry()
_upload_engine = UploadEngine()
_rule_engine = RuleEngineService()
_risk_engine = RiskEngineService()
_findings_engine = FindingsEngineService()
_report_engine = ReportEngineService()

PIPELINE_STEPS = [
    "upload",
    "validation",
    "rules",
    "risk",
    "findings",
    "ai_narrative",
    "report",
    "completion",
]

SUPPORTED_ENDPOINTS = [
    "upload",
    "run-rules",
    "run-risk",
    "risk-scores",
    "generate-findings",
    "findings",
    "reports",
    "reports/generate",
    "metadata",
    "workspace-config",
]


def _normalize_code(module_code: str) -> str:
    return module_code.strip().upper().replace("-", "_")


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (ModuleNotFoundError, ModuleNotBuiltError)):
        return HTTPException(status_code=404, detail=str(exc))
    return handle_service_error(exc)


def _resolve_provider(db: Session, module_code: str):
    try:
        return _registry.resolve_provider(db, _normalize_code(module_code))
    except (ModuleNotFoundError, ModuleNotBuiltError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{module_code}/metadata", response_model=ModuleMetadataOut)
def get_module_metadata(
    module_code: str,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del tenant
    try:
        provider = _resolve_provider(db, module_code)
        meta = provider.get_metadata()
        return ModuleMetadataOut(
            code=meta.code,
            name=meta.name,
            project_type=meta.project_type,
            slug=meta.slug,
            category=meta.category,
            icon=meta.icon,
            implementation_status=meta.implementation_status,
            input_format=meta.input_format,
            rule_prefix=meta.rule_prefix,
            theme_color=meta.theme_color,
            ui_config=meta.ui_config,
            plugin_config=meta.plugin_config,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_error(exc) from exc


@router.get("/{module_code}/workspace-config", response_model=ModuleWorkspaceConfigOut)
def get_workspace_config(
    module_code: str,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del tenant
    provider = _resolve_provider(db, module_code)
    meta = provider.get_metadata()
    return ModuleWorkspaceConfigOut(
        module_code=meta.code,
        metadata=ModuleMetadataOut(
            code=meta.code,
            name=meta.name,
            project_type=meta.project_type,
            slug=meta.slug,
            category=meta.category,
            icon=meta.icon,
            implementation_status=meta.implementation_status,
            input_format=meta.input_format,
            rule_prefix=meta.rule_prefix,
            theme_color=meta.theme_color,
            ui_config=meta.ui_config,
            plugin_config=meta.plugin_config,
        ),
        pipeline_steps=PIPELINE_STEPS,
        supported_endpoints=SUPPORTED_ENDPOINTS,
    )


@router.post("/{module_code}/upload", response_model=GenericUploadResponse)
async def upload_module_file(
    module_code: str,
    project_id: UUID = Query(..., description="Audit project UUID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    provider = _resolve_provider(db, module_code)
    content = await file.read()
    try:
        result = _upload_engine.upload(db, tenant, project_id, content, provider)
        return GenericUploadResponse(
            project_id=result.project_id,
            module_code=provider.code,
            validation=result.validation,
            records_imported=result.records_imported,
            message=result.message,
            extras=result.extras,
        )
    except HTTPException:
        raise
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{module_code}/run-rules", response_model=GenericRunRulesResponse)
def run_module_rules(
    module_code: str,
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    try:
        result = _rule_engine.run(db, project_id, provider)
        return GenericRunRulesResponse(
            project_id=result.project_id,
            module_code=provider.code,
            total_rules_run=result.total_rules_run,
            total_violations=result.total_violations,
            rule_summary=result.rule_summary,
            message=result.message,
        )
    except HTTPException:
        raise
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{module_code}/run-risk", response_model=GenericRunRiskResponse)
def run_module_risk(
    module_code: str,
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    try:
        result = _risk_engine.run(db, project_id, provider)
        return GenericRunRiskResponse(
            project_id=result.project_id,
            module_code=provider.code,
            total_scored=result.total_scored,
            high_risk=result.high_risk,
            medium_risk=result.medium_risk,
            low_risk=result.low_risk,
            message=result.message,
        )
    except HTTPException:
        raise
    except EvidenceGateViolation as exc:
        raise _handle_error(exc) from exc
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{module_code}/risk-scores")
def list_module_risk_scores(
    module_code: str,
    project_id: UUID = Query(...),
    risk_category: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    return provider.list_risk_scores(
        db, project_id, risk_category=risk_category, limit=limit, offset=offset
    )


@router.post("/{module_code}/generate-findings", response_model=GenericFindingsResponse)
def generate_module_findings(
    module_code: str,
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    try:
        findings = _findings_engine.generate(db, project_id, provider)
        items = [FindingOut.model_validate(f) for f in findings]
        return GenericFindingsResponse(
            project_id=project_id,
            module_code=provider.code,
            total=len(items),
            items=items,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{module_code}/findings", response_model=GenericFindingsResponse)
def list_module_findings(
    module_code: str,
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    findings = provider.list_findings(db, project_id)
    items = [FindingOut.model_validate(f) for f in findings]
    return GenericFindingsResponse(
        project_id=project_id,
        module_code=provider.code,
        total=len(items),
        items=items,
    )


@router.get("/{module_code}/reports", response_model=GenericReportsResponse)
def list_module_reports(
    module_code: str,
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    reports = (
        db.query(Report)
        .filter(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    items = [
        ReportOut(
            id=r.id,
            project_id=r.project_id,
            report_type=r.report_type,
            file_name=r.file_name,
            status=r.status,
            metadata=r.metadata_,
            created_at=r.created_at,
        )
        for r in reports
    ]
    return GenericReportsResponse(
        project_id=project_id,
        module_code=provider.code,
        items=items,
    )


@router.post("/{module_code}/reports/generate", response_model=GenericReportGenerateResponse)
def generate_module_report(
    module_code: str,
    project_id: UUID = Query(...),
    report_type: str | None = Query(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    provider = _resolve_provider(db, module_code)
    project = get_owned_project(db, project_id, tenant)
    provider.ensure_project_type(project)
    try:
        report = _report_engine.generate(
            db, project, tenant.user.id, provider, report_type
        )
        return GenericReportGenerateResponse(
            module_code=provider.code,
            report=ReportOut(
                id=report.id,
                project_id=report.project_id,
                report_type=report.report_type,
                file_name=report.file_name,
                status=report.status,
                metadata=report.metadata_,
                created_at=report.created_at,
            ),
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{module_code}/reports/{report_id}/download")
def download_module_report(
    module_code: str,
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del module_code
    report = (
        db.query(Report)
        .join(AuditProject)
        .join(AuditEngagement)
        .join(Client)
        .filter(Report.id == report_id, client_list_filter(tenant))
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path or not Path(report.file_path).is_file():
        raise HTTPException(status_code=404, detail="Report file not available")

    media = "application/octet-stream"
    if report.file_name.endswith(".pdf"):
        media = "application/pdf"
    elif report.file_name.endswith(".xlsx"):
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif report.file_name.endswith(".json"):
        media = "application/json"

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type=media,
    )
