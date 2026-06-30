from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.evidence import (
    EvidenceLinkCreate,
    EvidenceLinkOut,
    EvidenceListOut,
    EvidenceOut,
)
from app.services.audit_log_service import AuditLogService
from app.services.evidence_service import EvidenceService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Evidence"])
_evidence = EvidenceService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/{engagement_id}/evidence", response_model=EvidenceListOut)
def list_evidence(
    engagement_id: UUID,
    project_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query("active"),
    search: str | None = Query(None),
    current_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        result = _evidence.list_evidence(
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
        return EvidenceListOut(
            items=[EvidenceOut(**_evidence.to_out(e)) for e in result.items],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post("/{engagement_id}/evidence", response_model=EvidenceOut, status_code=201)
async def upload_evidence(
    engagement_id: UUID,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("other"),
    description: str | None = Form(None),
    project_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")
    content = await file.read()
    try:
        row = _evidence.upload_evidence(
            db,
            tenant,
            engagement_id,
            file_name=file.filename,
            content=content,
            content_type=file.content_type,
            title=title,
            category=category,
            description=description,
            project_id=project_id,
        )
        _audit_logs.write_log(
            db,
            action="evidence.upload",
            entity_type="evidence",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={"engagement_id": str(engagement_id), "title": title},
        )
        return EvidenceOut(**_evidence.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/evidence/{evidence_id}/versions",
    response_model=EvidenceOut,
    status_code=201,
)
async def upload_evidence_version(
    engagement_id: UUID,
    evidence_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")
    content = await file.read()
    try:
        row = _evidence.upload_new_version(
            db,
            tenant,
            engagement_id,
            evidence_id,
            file_name=file.filename,
            content=content,
            content_type=file.content_type,
        )
        _audit_logs.write_log(
            db,
            action="evidence.version",
            entity_type="evidence",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={"root_id": str(row.root_evidence_id), "version": row.version_number},
        )
        return EvidenceOut(**_evidence.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get(
    "/{engagement_id}/evidence/{evidence_id}/versions",
    response_model=list[EvidenceOut],
)
def list_evidence_versions(
    engagement_id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        rows = _evidence.list_versions(db, tenant, engagement_id, evidence_id)
        return [EvidenceOut(**_evidence.to_out(r)) for r in rows]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get(
    "/{engagement_id}/evidence/{evidence_id}/download",
)
def download_evidence(
    engagement_id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        path, evidence = _evidence.get_download_path(
            db, tenant, engagement_id, evidence_id
        )
        return FileResponse(
            path,
            filename=evidence.file_name,
            media_type=evidence.content_type or "application/octet-stream",
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/evidence/{evidence_id}/links",
    response_model=EvidenceLinkOut,
    status_code=201,
)
def create_evidence_link(
    engagement_id: UUID,
    evidence_id: UUID,
    body: EvidenceLinkCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        link = _evidence.create_link(
            db,
            tenant,
            engagement_id,
            evidence_id,
            linked_entity_type=body.linked_entity_type,
            linked_entity_id=body.linked_entity_id,
            link_type=body.link_type,
            finding_id=body.finding_id,
            workpaper_id=body.workpaper_id,
            notes=body.notes,
        )
        _audit_logs.write_log(
            db,
            action="evidence.link",
            entity_type="evidence_link",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=link.id,
            details={
                "evidence_id": str(evidence_id),
                "linked_entity_type": body.linked_entity_type,
                "linked_entity_id": str(body.linked_entity_id),
            },
        )
        return EvidenceLinkOut(**_evidence.link_to_out(link))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get(
    "/{engagement_id}/evidence/{evidence_id}/links",
    response_model=list[EvidenceLinkOut],
)
def list_evidence_links(
    engagement_id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        links = _evidence.list_links(db, tenant, engagement_id, evidence_id)
        return [EvidenceLinkOut(**_evidence.link_to_out(link)) for link in links]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
