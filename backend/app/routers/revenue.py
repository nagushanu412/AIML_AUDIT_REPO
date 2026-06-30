from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditFinding, AuditProject
from app.schemas.analytics import FindingOut
from app.schemas.revenue import (
    RevenueRiskScoreOut,
    RevenueRunRiskResponse,
    RevenueRunRulesResponse,
    RevenueUploadResponse,
)
from app.services.project_access import get_owned_project
from app.services.tenant_context import TenantContext
from app.services.revenue_findings_service import generate_revenue_findings
from app.services.revenue_risk_scoring import get_revenue_risk_scores, run_revenue_risk_scoring
from app.services.revenue_rule_runner import run_revenue_rules_for_project
from app.services.revenue_upload_service import save_revenue_invoices
from app.services.revenue_validator import validate_revenue_excel

router = APIRouter(prefix="/revenue", tags=["Revenue Testing"])
settings = get_settings()


def _ensure_revenue_project(project: AuditProject) -> None:
    if project.project_type != "revenue_testing":
        raise HTTPException(
            status_code=400,
            detail="This endpoint requires a revenue_testing project.",
        )


@router.post("/upload", response_model=RevenueUploadResponse)
async def upload_revenue_file(
    project_id: UUID = Query(..., description="Revenue testing project UUID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    content = await file.read()
    max_bytes = settings.max_upload_bytes
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_mb} MB.",
        )

    validation, df, total_taxable, total_gst, total_revenue = validate_revenue_excel(content)
    if not validation.is_valid or df is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Revenue file validation failed.",
                "validation": validation.model_dump(),
            },
        )

    count = save_revenue_invoices(db, project, df)
    return RevenueUploadResponse(
        project_id=project.id,
        validation=validation,
        invoices_imported=count,
        total_taxable=total_taxable,
        total_gst=total_gst,
        total_revenue=total_revenue,
        message=f"Imported {count} revenue invoices successfully.",
    )


@router.post("/run-rules", response_model=RevenueRunRulesResponse)
def run_revenue_rules(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)
    try:
        result = run_revenue_rules_for_project(db, project_id)
        return RevenueRunRulesResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-risk", response_model=RevenueRunRiskResponse)
def run_revenue_risk(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)
    try:
        result = run_revenue_risk_scoring(db, project_id)
        return RevenueRunRiskResponse(**result)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/risk-scores", response_model=list[RevenueRiskScoreOut])
def list_revenue_risk_scores(
    project_id: UUID = Query(...),
    risk_category: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)
    rows = get_revenue_risk_scores(
        db, project_id, risk_category=risk_category, limit=limit, offset=offset
    )
    return [
        RevenueRiskScoreOut(
            **row,
            invoice_date=row["invoice_date"].isoformat() if row.get("invoice_date") else None,
            total_amount=float(row["total_amount"]),
            gst_amount=float(row["gst_amount"]),
        )
        for row in rows
    ]


@router.post("/generate-findings", response_model=list[FindingOut])
def create_revenue_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)
    return generate_revenue_findings(db, project_id)


@router.get("/findings", response_model=list[FindingOut])
def list_revenue_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_revenue_project(project)
    return (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project_id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )
