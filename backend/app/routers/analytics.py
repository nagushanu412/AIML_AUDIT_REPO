from typing import Annotated
from uuid import UUID

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditEngagement, AuditProject, Client, Report
from app.schemas.analytics import FindingOut, ReportOut, RiskScoreOut, RunRiskResponse
from app.routers.errors import handle_service_error
from app.services.evidence_gate import EvidenceGateViolation
from app.services.module_framework.legacy_adapter import DEPRECATION_HEADERS, MODULE_CODES, legacy_adapter
from app.services.project_access import client_list_filter
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Analytics"])


@router.post("/run-risk", response_model=RunRiskResponse)
def run_risk(
    project_id: UUID = Query(..., description="Audit project UUID"),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "JOURNAL_ENTRY_TESTING")

    try:
        result = legacy_adapter.run_risk(db, tenant, MODULE_CODES["journal"], project_id)
        return RunRiskResponse(**result)
    except HTTPException:
        raise
    except EvidenceGateViolation as exc:
        raise handle_service_error(exc) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/risk-scores", response_model=list[RiskScoreOut])
def list_risk_scores(
    project_id: UUID = Query(...),
    risk_category: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    rows = legacy_adapter.list_risk_scores(
        db,
        tenant,
        MODULE_CODES["journal"],
        project_id,
        risk_category=risk_category,
        limit=limit,
        offset=offset,
    )
    return [RiskScoreOut(**row) for row in rows]


@router.post("/generate-findings", response_model=list[FindingOut])
def create_findings(
    project_id: UUID = Query(...),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "JOURNAL_ENTRY_TESTING")

    return legacy_adapter.generate_findings(
        db, tenant, MODULE_CODES["journal"], project_id
    )


@router.get("/findings", response_model=list[FindingOut])
def list_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    return legacy_adapter.list_findings(
        db, tenant, MODULE_CODES["journal"], project_id
    )


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    project_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    rows = legacy_adapter.list_reports(db, tenant, project_id)
    return [
        ReportOut(
            id=r.id,
            project_id=r.project_id,
            report_type=r.report_type,
            file_name=r.file_name,
            status=r.status,
            metadata=r.metadata_,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/reports/generate", response_model=ReportOut)
def create_report(
    project_id: UUID = Query(...),
    report_type: str = Query("journal_audit_summary"),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "JOURNAL_ENTRY_TESTING")

    report = legacy_adapter.generate_report(db, tenant, project_id, report_type)
    return ReportOut(
        id=report.id,
        project_id=report.project_id,
        report_type=report.report_type,
        file_name=report.file_name,
        status=report.status,
        metadata=report.metadata_,
        created_at=report.created_at,
    )


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
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
