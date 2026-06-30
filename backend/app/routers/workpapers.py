from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.workpaper import (
    WorkpaperCreate,
    WorkpaperListOut,
    WorkpaperOut,
    WorkpaperUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.tenant_context import TenantContext
from app.services.workpaper_service import WorkpaperService

router = APIRouter(prefix="/engagements", tags=["Workpapers"])
_workpapers = WorkpaperService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/{engagement_id}/workpapers", response_model=WorkpaperListOut)
def list_workpapers(
    engagement_id: UUID,
    project_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    current_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        result = _workpapers.list_workpapers(
            db,
            tenant,
            engagement_id,
            project_id=project_id,
            category=category,
            status=status,
            search=search,
            current_only=current_only,
            limit=limit,
            offset=offset,
        )
        return WorkpaperListOut(
            items=[WorkpaperOut(**_workpapers.to_out(w)) for w in result.items],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/workpapers",
    response_model=WorkpaperOut,
    status_code=status.HTTP_201_CREATED,
)
def create_workpaper(
    engagement_id: UUID,
    body: WorkpaperCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        row = _workpapers.create_workpaper(
            db,
            tenant,
            engagement_id,
            reference_code=body.reference_code,
            title=body.title,
            category=body.category,
            description=body.description,
            status=body.status,
            project_id=body.project_id,
            metadata=body.metadata,
        )
        _audit_logs.write_log(
            db,
            action="workpaper.create",
            entity_type="workpaper",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={"reference_code": row.reference_code},
        )
        return WorkpaperOut(**_workpapers.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch(
    "/{engagement_id}/workpapers/{workpaper_id}",
    response_model=WorkpaperOut,
)
def update_workpaper(
    engagement_id: UUID,
    workpaper_id: UUID,
    body: WorkpaperUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        row = _workpapers.update_workpaper(
            db,
            tenant,
            engagement_id,
            workpaper_id,
            title=body.title,
            description=body.description,
            category=body.category,
            status=body.status,
            metadata=body.metadata,
        )
        _audit_logs.write_log(
            db,
            action="workpaper.update",
            entity_type="workpaper",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=workpaper_id,
            details={"reference_code": row.reference_code},
        )
        return WorkpaperOut(**_workpapers.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/workpapers/{workpaper_id}/upload",
    response_model=WorkpaperOut,
)
async def upload_workpaper_file(
    engagement_id: UUID,
    workpaper_id: UUID,
    file: UploadFile = File(...),
    new_version: bool = Form(False),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")
    content = await file.read()
    try:
        row = _workpapers.upload_workpaper_file(
            db,
            tenant,
            engagement_id,
            workpaper_id,
            file_name=file.filename,
            content=content,
            content_type=file.content_type,
            new_version=new_version,
        )
        _audit_logs.write_log(
            db,
            action="workpaper.upload",
            entity_type="workpaper",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={"version": row.version_number},
        )
        return WorkpaperOut(**_workpapers.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get(
    "/{engagement_id}/workpapers/{workpaper_id}/versions",
    response_model=list[WorkpaperOut],
)
def list_workpaper_versions(
    engagement_id: UUID,
    workpaper_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        rows = _workpapers.list_versions(db, tenant, engagement_id, workpaper_id)
        return [WorkpaperOut(**_workpapers.to_out(r)) for r in rows]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{engagement_id}/workpapers/{workpaper_id}/download")
def download_workpaper(
    engagement_id: UUID,
    workpaper_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        path, workpaper = _workpapers.get_download_path(
            db, tenant, engagement_id, workpaper_id
        )
        return FileResponse(
            path,
            filename=workpaper.file_name or "workpaper",
            media_type=workpaper.content_type or "application/octet-stream",
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
