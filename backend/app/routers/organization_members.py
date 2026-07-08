from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import OrganizationMember, User
from app.schemas.member import MemberInvite, MemberOut, MemberUpdate
from app.services.audit_log_service import AuditLogService
from app.services.invite_service import send_member_invite_email
from app.services.member_service import MemberService

router = APIRouter(prefix="/organizations", tags=["Organization Members"])
_member_service = MemberService()
_audit_logs = AuditLogService()


def _handle_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


def _member_to_out(
    member: OrganizationMember,
    *,
    invite_email_sent: bool = False,
    invite_link: str | None = None,
) -> MemberOut:
    user = member.user
    return MemberOut(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        email=user.email if user else "",
        full_name=user.full_name if user else "",
        role=member.role,
        status=member.status,
        invited_at=member.invited_at,
        joined_at=member.joined_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
        invite_email_sent=invite_email_sent,
        invite_link=invite_link,
    )


def _invite_and_notify(
    db: Session,
    current_user: User,
    organization_id: UUID,
    body: MemberInvite,
) -> MemberOut:
    result = _member_service.invite_member(
        db,
        current_user,
        organization_id,
        email=body.email,
        role=body.role,
        full_name=body.full_name,
    )
    email_result = send_member_invite_email(
        db,
        result.member,
        inviter=current_user,
        is_new_user=result.is_new_user,
    )
    invite_link = email_result.invite_link if not email_result.sent else None
    _audit_logs.write_log(
        db,
        action="member.invite",
        entity_type="organization_member",
        user_id=current_user.id,
        organization_id=organization_id,
        entity_id=result.member.id,
        details={"email": body.email, "role": body.role},
    )
    return _member_to_out(
        result.member,
        invite_email_sent=email_result.sent,
        invite_link=invite_link,
    )


def _resolve_organization_id(
    db: Session, user: User, organization_id: UUID | None
) -> UUID:
    if organization_id is not None:
        return organization_id
    org_id = _member_service.resolve_user_organization_id(db, user)
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization linked to this account yet.",
        )
    return org_id


@router.get("/me/members", response_model=list[MemberOut])
def list_my_organization_members(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    org_id = _resolve_organization_id(db, current_user, None)
    try:
        members = _member_service.list_members(db, current_user, org_id)
        return [_member_to_out(m) for m in members]
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.post("/me/members/invite", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def invite_my_organization_member(
    body: MemberInvite,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    org_id = _resolve_organization_id(db, current_user, None)
    try:
        return _invite_and_notify(db, current_user, org_id, body)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.get("/{organization_id}/members", response_model=list[MemberOut])
def list_organization_members(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        members = _member_service.list_members(db, current_user, organization_id)
        return [_member_to_out(m) for m in members]
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.post(
    "/{organization_id}/members/invite",
    response_model=MemberOut,
    status_code=status.HTTP_201_CREATED,
)
def invite_organization_member(
    organization_id: UUID,
    body: MemberInvite,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _invite_and_notify(db, current_user, organization_id, body)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.patch("/me/members/{member_id}", response_model=MemberOut)
def update_my_organization_member(
    member_id: UUID,
    body: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    org_id = _resolve_organization_id(db, current_user, None)
    try:
        member = _member_service.update_member(
            db,
            current_user,
            org_id,
            member_id,
            role=body.role,
            status=body.status,
        )
        _audit_logs.write_log(
            db,
            action="member.update",
            entity_type="organization_member",
            user_id=current_user.id,
            organization_id=org_id,
            entity_id=member.id,
            details={"role": member.role, "status": member.status},
        )
        return _member_to_out(member)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.patch("/{organization_id}/members/{member_id}", response_model=MemberOut)
def update_organization_member(
    organization_id: UUID,
    member_id: UUID,
    body: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        member = _member_service.update_member(
            db,
            current_user,
            organization_id,
            member_id,
            role=body.role,
            status=body.status,
        )
        _audit_logs.write_log(
            db,
            action="member.update",
            entity_type="organization_member",
            user_id=current_user.id,
            organization_id=organization_id,
            entity_id=member.id,
            details={"role": member.role, "status": member.status},
        )
        return _member_to_out(member)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.delete("/me/members/{member_id}", response_model=MemberOut)
def remove_my_organization_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    org_id = _resolve_organization_id(db, current_user, None)
    try:
        member = _member_service.remove_member(db, current_user, org_id, member_id)
        _audit_logs.write_log(
            db,
            action="member.remove",
            entity_type="organization_member",
            user_id=current_user.id,
            organization_id=org_id,
            entity_id=member.id,
            details={"status": member.status},
        )
        return _member_to_out(member)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.delete("/{organization_id}/members/{member_id}", response_model=MemberOut)
def remove_organization_member(
    organization_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        member = _member_service.remove_member(
            db, current_user, organization_id, member_id
        )
        _audit_logs.write_log(
            db,
            action="member.remove",
            entity_type="organization_member",
            user_id=current_user.id,
            organization_id=organization_id,
            entity_id=member.id,
            details={"status": member.status},
        )
        return _member_to_out(member)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc
