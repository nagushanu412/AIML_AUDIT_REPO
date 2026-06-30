from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.audit_log import AuditLogOut
from app.services.audit_log_service import AuditLogService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
_log_service = AuditLogService()


@router.get("/me", response_model=list[AuditLogOut])
def list_my_organization_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    if not tenant.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization linked to this account.",
        )
    return _log_service.list_for_organization(
        db, tenant.organization_id, limit=limit, offset=offset
    )
