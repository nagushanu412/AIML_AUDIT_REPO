from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditFinding, AuditProject
from app.schemas.analytics import FindingOut
from app.schemas.procurement import (
    ProcurementRiskScoreOut,
    ProcurementRunRiskResponse,
    ProcurementRunRulesResponse,
    ProcurementUploadResponse,
)
from app.services.project_access import get_owned_project
from app.services.tenant_context import TenantContext
from app.services.procurement_findings_service import generate_procurement_findings
from app.services.procurement_risk_scoring import (
    get_procurement_risk_scores,
    run_procurement_risk_scoring,
)
from app.services.procurement_rule_runner import run_procurement_rules_for_project
from app.services.procurement_upload_service import save_procurement_invoices
from app.services.procurement_validator import validate_procurement_excel

router = APIRouter(prefix="/procurement", tags=["Procurement Testing"])
settings = get_settings()


def _ensure_procurement_project(project: AuditProject) -> None:
    if project.project_type != "procurement_testing":
        raise HTTPException(
            status_code=400,
            detail="This endpoint requires a procurement_testing project.",
        )


@router.post("/upload", response_model=ProcurementUploadResponse)
async def upload_procurement_file(
    project_id: UUID = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB.")

    validation, df, total_taxable, total_gst, total_spend = validate_procurement_excel(content)
    if not validation.is_valid or df is None:
        raise HTTPException(
            status_code=422,
            detail={"message": "Procurement file validation failed.", "validation": validation.model_dump()},
        )

    count = save_procurement_invoices(db, project, df)
    return ProcurementUploadResponse(
        project_id=project.id,
        validation=validation,
        invoices_imported=count,
        total_taxable=total_taxable,
        total_gst=total_gst,
        total_spend=total_spend,
        message=f"Imported {count} vendor invoices successfully.",
    )


@router.post("/run-rules", response_model=ProcurementRunRulesResponse)
def run_procurement_rules(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    try:
        return ProcurementRunRulesResponse(**run_procurement_rules_for_project(db, project_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-risk", response_model=ProcurementRunRiskResponse)
def run_procurement_risk(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    try:
        return ProcurementRunRiskResponse(**run_procurement_risk_scoring(db, project_id))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/risk-scores", response_model=list[ProcurementRiskScoreOut])
def list_procurement_risk_scores(
    project_id: UUID = Query(...),
    risk_category: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    rows = get_procurement_risk_scores(
        db, project_id, risk_category=risk_category, limit=limit, offset=offset
    )
    return [
        ProcurementRiskScoreOut(
            **row,
            invoice_date=row["invoice_date"].isoformat() if row.get("invoice_date") else None,
            total_amount=float(row["total_amount"]),
            gst_amount=float(row["gst_amount"]),
        )
        for row in rows
    ]


@router.post("/generate-findings", response_model=list[FindingOut])
def create_procurement_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    return generate_procurement_findings(db, project_id)


@router.get("/findings", response_model=list[FindingOut])
def list_procurement_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    return (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project_id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )
