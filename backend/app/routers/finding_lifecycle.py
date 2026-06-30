from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.finding_lifecycle import (
    FindingHistoryOut,
    FindingLifecycleOut,
    FindingListOut,
    FindingStatusUpdate,
    ManagementResponseUpdate,
    RemediationUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.finding_lifecycle_service import FindingLifecycleService
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Finding Lifecycle"])
_findings = FindingLifecycleService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/engagements/{engagement_id}/findings", response_model=FindingListOut)
def list_engagement_findings(
    engagement_id: UUID,
    finding_status: str | None = Query(None, alias="status"),
    risk_level: str | None = Query(None),
    project_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        result = _findings.list_engagement_findings(
            db,
            tenant,
            engagement_id,
            status=finding_status,
            risk_level=risk_level,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
        return FindingListOut(
            items=[
                FindingLifecycleOut(**_findings.to_out(f)) for f in result.items
            ],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/findings/{finding_id}", response_model=FindingLifecycleOut)
def get_finding(
    finding_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        finding = _findings.get_finding(db, tenant, finding_id)
        return FindingLifecycleOut(**_findings.to_out(finding))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch("/findings/{finding_id}/status", response_model=FindingLifecycleOut)
def update_finding_status(
    finding_id: UUID,
    body: FindingStatusUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        finding = _findings.update_status(
            db,
            tenant,
            finding_id,
            status=body.status,
            change_reason=body.change_reason,
        )
        _audit_logs.write_log(
            db,
            action="finding.status_change",
            entity_type="finding",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=finding_id,
            details={"status": finding.status},
        )
        return FindingLifecycleOut(**_findings.to_out(finding))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch(
    "/findings/{finding_id}/management-response",
    response_model=FindingLifecycleOut,
)
def update_management_response(
    finding_id: UUID,
    body: ManagementResponseUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        finding = _findings.set_management_response(
            db,
            tenant,
            finding_id,
            response=body.response,
            change_reason=body.change_reason,
        )
        _audit_logs.write_log(
            db,
            action="finding.management_response",
            entity_type="finding",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=finding_id,
        )
        return FindingLifecycleOut(**_findings.to_out(finding))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch("/findings/{finding_id}/remediation", response_model=FindingLifecycleOut)
def update_remediation(
    finding_id: UUID,
    body: RemediationUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        finding = _findings.update_remediation(
            db,
            tenant,
            finding_id,
            remediation_status=body.remediation_status,
            remediation_notes=body.remediation_notes,
            remediation_due_date=body.remediation_due_date,
            change_reason=body.change_reason,
        )
        _audit_logs.write_log(
            db,
            action="finding.remediation",
            entity_type="finding",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=finding_id,
            details={"remediation_status": finding.remediation_status},
        )
        return FindingLifecycleOut(**_findings.to_out(finding))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/findings/{finding_id}/history", response_model=list[FindingHistoryOut])
def list_finding_history(
    finding_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        entries = _findings.list_history(
            db, tenant, finding_id, limit=limit, offset=offset
        )
        return [FindingHistoryOut(**_findings.history_to_out(e)) for e in entries]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
