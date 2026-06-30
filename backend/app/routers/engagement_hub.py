from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.services.audit_log_service import AuditLogService
from app.services.engagement_hub_service import EngagementHubService, EngagementReportService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Engagement Hub"])
_hub = EngagementHubService()
_reports = EngagementReportService()
_audit_logs = AuditLogService()


class EngagementHubOut(BaseModel):
    engagement_id: UUID
    financial_year: str
    status: str
    enabled_modules: list
    team_summary: dict
    official_runs: list
    latest_runs: list
    findings_count: int
    pending_actions: list[str]


class EngagementReportOut(BaseModel):
    id: UUID
    engagement_id: UUID
    report_type: str
    version_number: int
    is_official: bool
    file_name: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/{engagement_id}/hub", response_model=EngagementHubOut)
def get_engagement_hub(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        return EngagementHubOut(**_hub.get_hub_summary(db, tenant, engagement_id))
    except ValueError as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/reports/consolidated",
    response_model=EngagementReportOut,
    status_code=201,
)
def generate_engagement_report(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        row = _reports.generate_consolidated_report(db, tenant, engagement_id)
        _audit_logs.write_log(
            db,
            action="report.generate",
            entity_type="report_history",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=row.id,
            details={"report_type": row.report_type},
        )
        out = EngagementReportService.to_out(row)
        return EngagementReportOut(**out)
    except ValueError as exc:
        raise _handle_error(exc) from exc
