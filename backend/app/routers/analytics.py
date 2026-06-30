from typing import Annotated
from uuid import UUID

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditEngagement, AuditFinding, AuditProject, Client, Report
from app.schemas.analytics import FindingOut, ReportOut, RiskScoreOut, RunRiskResponse
from app.services.findings_service import generate_findings
from app.services.project_access import client_list_filter, get_owned_project
from app.services.report_service import generate_project_report
from app.services.risk_scoring import get_risk_scores, run_risk_scoring
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Analytics"])


@router.post("/run-risk", response_model=RunRiskResponse)
def run_risk(
    project_id: UUID = Query(..., description="Audit project UUID"),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    get_owned_project(db, project_id, tenant)
    try:
        return run_risk_scoring(db, project_id)
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
    get_owned_project(db, project_id, tenant)
    rows = get_risk_scores(
        db, project_id, risk_category=risk_category, limit=limit, offset=offset
    )
    return [RiskScoreOut(**row) for row in rows]


@router.post("/generate-findings", response_model=list[FindingOut])
def create_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    get_owned_project(db, project_id, tenant)
    findings = generate_findings(db, project_id)
    return findings


@router.get("/findings", response_model=list[FindingOut])
def list_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    get_owned_project(db, project_id, tenant)
    return (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project_id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    project_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    query = (
        db.query(Report)
        .join(AuditProject)
        .join(AuditEngagement)
        .join(Client)
        .filter(client_list_filter(tenant))
    )
    if project_id:
        get_owned_project(db, project_id, tenant)
        query = query.filter(Report.project_id == project_id)
    rows = query.order_by(Report.created_at.desc()).limit(100).all()
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
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    report = generate_project_report(db, project, tenant.user.id, report_type)
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
