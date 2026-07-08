from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_tenant_context
from app.models.audit import AuditModuleCatalog, ModuleAnalysisRun
from app.routers.errors import handle_service_error
from app.services.analysis_run_service import AnalysisRunService, SUGGESTED_RUN_NAMES
from app.services.audit_log_service import AuditLogService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Analysis Runs"])
_runs = AnalysisRunService()
_audit_logs = AuditLogService()


class AnalysisRunCreate(BaseModel):
    module_code: str = Field(..., min_length=1)
    run_name: str | None = Field(None, max_length=255)
    project_id: UUID | None = None


class AnalysisRunOut(BaseModel):
    id: UUID
    engagement_id: UUID
    project_id: UUID | None
    module_catalog_id: UUID | None
    module_code: str | None
    run_name: str
    status: str
    is_official: bool
    job_id: str | None
    progress_pct: int
    progress_message: str | None
    error_message: str | None
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AnalysisRunListOut(BaseModel):
    items: list[AnalysisRunOut]
    total: int
    suggested_names: list[str]


def _handle_error(exc: Exception) -> HTTPException:
    return handle_service_error(exc)


def _process_run_background(run_id: UUID) -> None:
    db = SessionLocal()
    try:
        run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
        if not run:
            return
        run.progress_pct = 50
        run.progress_message = "Running rules and risk scoring"
        db.commit()

        run.progress_pct = 100
        run.status = "completed"
        run.progress_message = "Analysis completed"
        run.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
        if run:
            run.status = "draft"
            run.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.get("/{engagement_id}/runs", response_model=AnalysisRunListOut)
def list_analysis_runs(
    engagement_id: UUID,
    module_code: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        items, total = _runs.list_runs(
            db,
            tenant,
            engagement_id,
            module_code=module_code,
            status=status,
            limit=limit,
            offset=offset,
        )
        module_map = {}
        for run in items:
            if run.module_catalog_id and run.module_catalog_id not in module_map:
                mod = (
                    db.query(AuditModuleCatalog)
                    .filter(AuditModuleCatalog.id == run.module_catalog_id)
                    .first()
                )
                module_map[run.module_catalog_id] = mod
        return AnalysisRunListOut(
            items=[
                AnalysisRunOut(
                    **_runs.to_out(r, module_map.get(r.module_catalog_id))
                )
                for r in items
            ],
            total=total,
            suggested_names=SUGGESTED_RUN_NAMES,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/runs",
    response_model=AnalysisRunOut,
    status_code=201,
)
def create_analysis_run(
    engagement_id: UUID,
    body: AnalysisRunCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        run = _runs.create_run(
            db,
            tenant,
            engagement_id,
            module_code=body.module_code,
            run_name=body.run_name,
            project_id=body.project_id,
        )
        module = (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.id == run.module_catalog_id)
            .first()
        )
        return AnalysisRunOut(**_runs.to_out(run, module))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post("/{engagement_id}/runs/{run_id}/start", response_model=AnalysisRunOut)
def start_analysis_run(
    engagement_id: UUID,
    run_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        run = _runs.start_run(db, tenant, run_id)
        background_tasks.add_task(_process_run_background, run.id)
        _audit_logs.write_log(
            db,
            action="analysis.start",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        module = (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.id == run.module_catalog_id)
            .first()
        )
        return AnalysisRunOut(**_runs.to_out(run, module))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{engagement_id}/runs/{run_id}", response_model=AnalysisRunOut)
def get_analysis_run(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        run = _runs.get_run(db, tenant, run_id)
        module = (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.id == run.module_catalog_id)
            .first()
        )
        return AnalysisRunOut(**_runs.to_out(run, module))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


def _run_out(db: Session, run: ModuleAnalysisRun) -> AnalysisRunOut:
    module = (
        db.query(AuditModuleCatalog)
        .filter(AuditModuleCatalog.id == run.module_catalog_id)
        .first()
    )
    return AnalysisRunOut(**_runs.to_out(run, module))


@router.post(
    "/{engagement_id}/runs/{run_id}/submit-review",
    response_model=AnalysisRunOut,
)
def submit_analysis_run_for_review(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del engagement_id
    try:
        run = _runs.submit_for_review(db, tenant, run_id)
        _audit_logs.write_log(
            db,
            action="analysis.submit_review",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        return _run_out(db, run)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/runs/{run_id}/approve",
    response_model=AnalysisRunOut,
)
def approve_analysis_run(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del engagement_id
    try:
        run = _runs.approve_run(db, tenant, run_id)
        _audit_logs.write_log(
            db,
            action="analysis.approve",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        return _run_out(db, run)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/runs/{run_id}/return",
    response_model=AnalysisRunOut,
)
def return_analysis_run_to_auditor(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del engagement_id
    try:
        run = _runs.return_to_auditor(db, tenant, run_id)
        _audit_logs.write_log(
            db,
            action="analysis.return",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        return _run_out(db, run)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/runs/{run_id}/designate-official",
    response_model=AnalysisRunOut,
)
def designate_official_analysis_run(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del engagement_id
    try:
        run = _runs.designate_official(db, tenant, run_id)
        _audit_logs.write_log(
            db,
            action="analysis.official_designated",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        return _run_out(db, run)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/runs/{run_id}/archive",
    response_model=AnalysisRunOut,
)
def archive_analysis_run(
    engagement_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    del engagement_id
    try:
        run = _runs.archive_run(db, tenant, run_id)
        _audit_logs.write_log(
            db,
            action="analysis.archive",
            entity_type="module_analysis_run",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=run_id,
        )
        return _run_out(db, run)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
