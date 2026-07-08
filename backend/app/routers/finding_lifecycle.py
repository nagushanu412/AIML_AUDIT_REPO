from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.routers.errors import handle_service_error
from app.schemas.finding_lifecycle import (
    FindingHistoryOut,
    FindingLifecycleOut,
    FindingListOut,
    FindingRelationshipCreate,
    FindingRelationshipOut,
    FindingStatusUpdate,
    ManagementResponseUpdate,
    RemediationUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.finding_lifecycle_service import FindingLifecycleService
from app.services.finding_relationship_service import FindingRelationshipService
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Finding Lifecycle"])
_findings = FindingLifecycleService()
_relationships = FindingRelationshipService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    return handle_service_error(exc)


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


@router.get(
    "/findings/{finding_id}/relationships",
    response_model=list[FindingRelationshipOut],
)
def list_finding_relationships(
    finding_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        rows = _relationships.list_relationships(db, tenant, finding_id)
        return [FindingRelationshipOut(**_relationships.to_out(r)) for r in rows]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/findings/{finding_id}/relationships",
    response_model=FindingRelationshipOut,
    status_code=201,
)
def create_finding_relationship(
    finding_id: UUID,
    body: FindingRelationshipCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        row = _relationships.create_relationship(
            db,
            tenant,
            finding_id,
            target_finding_id=body.target_finding_id,
            relationship_type=body.relationship_type,
            notes=body.notes,
        )
        _audit_logs.write_log(
            db,
            action="finding.relationship_create",
            entity_type="finding_relationship",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={
                "source_finding_id": str(finding_id),
                "target_finding_id": str(body.target_finding_id),
                "relationship_type": row.relationship_type,
            },
        )
        return FindingRelationshipOut(**_relationships.to_out(row))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.delete(
    "/findings/{finding_id}/relationships/{relationship_id}",
    status_code=204,
)
def delete_finding_relationship(
    finding_id: UUID,
    relationship_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        _relationships.delete_relationship(db, tenant, finding_id, relationship_id)
        _audit_logs.write_log(
            db,
            action="finding.relationship_delete",
            entity_type="finding_relationship",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=relationship_id,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
