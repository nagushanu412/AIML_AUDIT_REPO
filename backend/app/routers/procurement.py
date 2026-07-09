from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditProject
from app.schemas.analytics import FindingOut
from app.schemas.procurement import (
    ProcurementRiskScoreOut,
    ProcurementRunRiskResponse,
    ProcurementRunRulesResponse,
    ProcurementUploadResponse,
)
from app.services.module_framework.legacy_adapter import DEPRECATION_HEADERS, MODULE_CODES, legacy_adapter
from app.services.project_access import get_owned_project
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/procurement", tags=["Procurement Testing"])


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
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "PROCUREMENT_TESTING")

    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    legacy_adapter.validate_xlsx(file.filename)
    content = await file.read()
    legacy_adapter.validate_size(content)
    return legacy_adapter.invoice_upload(db, tenant, "procurement", project_id, content)


@router.post("/run-rules", response_model=ProcurementRunRulesResponse)
def run_procurement_rules(
    project_id: UUID = Query(...),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "PROCUREMENT_TESTING")

    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    try:
        result = legacy_adapter.run_rules(
            db, tenant, MODULE_CODES["procurement"], project_id
        )
        return ProcurementRunRulesResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-risk", response_model=ProcurementRunRiskResponse)
def run_procurement_risk(
    project_id: UUID = Query(...),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "PROCUREMENT_TESTING")

    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    try:
        result = legacy_adapter.run_risk(
            db, tenant, MODULE_CODES["procurement"], project_id
        )
        return ProcurementRunRiskResponse(**result)
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
    rows = legacy_adapter.list_risk_scores(
        db,
        tenant,
        MODULE_CODES["procurement"],
        project_id,
        risk_category=risk_category,
        limit=limit,
        offset=offset,
    )
    return legacy_adapter.map_procurement_risk_scores(rows)


@router.post("/generate-findings", response_model=list[FindingOut])
def create_procurement_findings(
    project_id: UUID = Query(...),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "PROCUREMENT_TESTING")

    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    return legacy_adapter.generate_findings(
        db, tenant, MODULE_CODES["procurement"], project_id
    )


@router.get("/findings", response_model=list[FindingOut])
def list_procurement_findings(
    project_id: UUID = Query(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    _ensure_procurement_project(project)
    return legacy_adapter.list_findings(
        db, tenant, MODULE_CODES["procurement"], project_id
    )
