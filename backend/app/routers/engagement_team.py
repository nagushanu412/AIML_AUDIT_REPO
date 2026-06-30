from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.engagement_team import (
    EngagementTeamAssign,
    EngagementTeamHistoryListOut,
    EngagementTeamHistoryOut,
    EngagementTeamListOut,
    EngagementTeamMemberOut,
    EngagementTeamSummaryOut,
    EngagementTeamUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.engagement_team_service import EngagementTeamService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Engagement Team"])
_team_service = EngagementTeamService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


def _write_team_audit_log(
    db: Session,
    tenant: TenantContext,
    engagement_id: UUID,
    action: str,
    details: dict,
) -> None:
    _audit_logs.write_log(
        db,
        action=action,
        entity_type="engagement_team",
        user_id=tenant.user.id,
        organization_id=tenant.organization_id,
        entity_id=engagement_id,
        details=details,
    )


@router.get("/{engagement_id}/team", response_model=EngagementTeamListOut)
def list_engagement_team(
    engagement_id: UUID,
    role: str | None = Query(None),
    status: str | None = Query("active"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        result = _team_service.list_team_members(
            db,
            tenant,
            engagement_id,
            role=role,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )
        return EngagementTeamListOut(
            items=[
                EngagementTeamMemberOut(**_team_service.member_to_out(m))
                for m in result.items
            ],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{engagement_id}/team/summary", response_model=EngagementTeamSummaryOut)
def get_engagement_team_summary(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        summary = _team_service.get_team_summary(db, tenant, engagement_id)
        return EngagementTeamSummaryOut(
            engagement_id=summary["engagement_id"],
            total_active=summary["total_active"],
            partner=(
                EngagementTeamMemberOut(**summary["partner"])
                if summary["partner"]
                else None
            ),
            audit_manager=(
                EngagementTeamMemberOut(**summary["audit_manager"])
                if summary["audit_manager"]
                else None
            ),
            by_role={
                role: [EngagementTeamMemberOut(**item) for item in items]
                for role, items in summary["by_role"].items()
            },
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/team",
    response_model=EngagementTeamMemberOut,
    status_code=status.HTTP_201_CREATED,
)
def assign_engagement_team_member(
    engagement_id: UUID,
    body: EngagementTeamAssign,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        member = _team_service.assign_member(
            db,
            tenant,
            engagement_id,
            user_id=body.user_id,
            role=body.role,
            notes=body.notes,
            change_reason=body.change_reason,
        )
        _write_team_audit_log(
            db,
            tenant,
            engagement_id,
            "team.assign",
            {
                "user_id": str(body.user_id),
                "role": body.role,
                "team_member_id": str(member.id),
            },
        )
        return EngagementTeamMemberOut(**_team_service.member_to_out(member))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch(
    "/{engagement_id}/team/{member_id}",
    response_model=EngagementTeamMemberOut,
)
def update_engagement_team_member(
    engagement_id: UUID,
    member_id: UUID,
    body: EngagementTeamUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        member = _team_service.update_assignment(
            db,
            tenant,
            engagement_id,
            member_id,
            role=body.role,
            notes=body.notes,
            change_reason=body.change_reason,
        )
        _write_team_audit_log(
            db,
            tenant,
            engagement_id,
            "team.update",
            {
                "team_member_id": str(member_id),
                "role": member.role,
            },
        )
        return EngagementTeamMemberOut(**_team_service.member_to_out(member))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.delete(
    "/{engagement_id}/team/{member_id}",
    response_model=EngagementTeamMemberOut,
)
def remove_engagement_team_member(
    engagement_id: UUID,
    member_id: UUID,
    change_reason: str | None = Query(None, max_length=2000),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        member = _team_service.remove_member(
            db,
            tenant,
            engagement_id,
            member_id,
            change_reason=change_reason,
        )
        _write_team_audit_log(
            db,
            tenant,
            engagement_id,
            "team.remove",
            {
                "team_member_id": str(member_id),
                "user_id": str(member.user_id),
                "role": member.role,
            },
        )
        return EngagementTeamMemberOut(**_team_service.member_to_out(member))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/{engagement_id}/team/history", response_model=EngagementTeamHistoryListOut)
def list_engagement_team_history(
    engagement_id: UUID,
    user_id: UUID | None = Query(None),
    role: str | None = Query(None),
    action: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        result = _team_service.list_assignment_history(
            db,
            tenant,
            engagement_id,
            user_id=user_id,
            role=role,
            action=action,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        return EngagementTeamHistoryListOut(
            items=[
                EngagementTeamHistoryOut(**_team_service.history_to_out(entry))
                for entry in result.items
            ],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
