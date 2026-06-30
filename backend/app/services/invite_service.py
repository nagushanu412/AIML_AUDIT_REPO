from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import Organization, OrganizationMember, User
from app.services.auth_service import AUDITOR_PORTAL_ROLES, hash_password, issue_tokens
from app.services.email_service import EmailDeliveryResult, send_email
from app.services.member_constants import ROLE_LABELS

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class InviteEmailResult:
    sent: bool
    invite_link: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class InvitePreview:
    email: str
    full_name: str
    organization_name: str
    role: str
    role_label: str
    requires_password: bool


def create_invite_token(
    *,
    member_id: uuid.UUID,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    email: str,
    is_new_user: bool,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.invite_token_expire_days)
    payload = {
        "sub": str(user_id),
        "member_id": str(member_id),
        "org_id": str(organization_id),
        "email": email,
        "is_new_user": is_new_user,
        "type": "invite",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_invite_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise ValueError("This invitation link is invalid or has expired.") from exc
    if payload.get("type") != "invite":
        raise ValueError("This invitation link is invalid or has expired.")
    return payload


def build_invite_link(token: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/accept-invite?token={token}"


def preview_invite(db: Session, token: str) -> InvitePreview:
    payload = decode_invite_token(token)
    member = _load_invited_member(db, payload)
    organization = db.query(Organization).filter(Organization.id == member.organization_id).first()
    user = member.user
    if not organization or not user:
        raise ValueError("This invitation is no longer valid.")

    role = member.role
    return InvitePreview(
        email=user.email,
        full_name=user.full_name,
        organization_name=organization.name,
        role=role,
        role_label=ROLE_LABELS.get(role, role.replace("_", " ").title()),
        requires_password=bool(payload.get("is_new_user")),
    )


def accept_invite(
    db: Session,
    token: str,
    password: str | None = None,
) -> tuple[dict | None, str]:
    payload = decode_invite_token(token)
    member = _load_invited_member(db, payload)
    user = member.user
    if not user:
        raise ValueError("This invitation is no longer valid.")

    is_new_user = bool(payload.get("is_new_user"))
    if is_new_user:
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        user.password_hash = hash_password(password)
    elif password:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        user.password_hash = hash_password(password)

    now = datetime.now(timezone.utc)
    member.status = "active"
    if not member.joined_at:
        member.joined_at = now

    db.commit()
    db.refresh(user)
    db.refresh(member)

    if user.role not in AUDITOR_PORTAL_ROLES:
        raise ValueError("This account cannot access the auditor portal.")

    if is_new_user or password:
        return issue_tokens(db, user), "Welcome to AuditAI Platform. Redirecting to dashboard…"

    login_url = f"{settings.frontend_url.rstrip('/')}/?email={user.email}"
    return None, f"Invitation accepted. Sign in at {login_url} to continue."


def send_member_invite_email(
    db: Session,
    member: OrganizationMember,
    *,
    inviter: User,
    is_new_user: bool,
) -> InviteEmailResult:
    organization = (
        db.query(Organization).filter(Organization.id == member.organization_id).first()
    )
    user = member.user
    if not organization or not user:
        return InviteEmailResult(sent=False, error="Missing organization or user for invite email.")

    token = create_invite_token(
        member_id=member.id,
        user_id=user.id,
        organization_id=member.organization_id,
        email=user.email,
        is_new_user=is_new_user,
    )
    invite_link = build_invite_link(token)
    role_label = ROLE_LABELS.get(member.role, member.role.replace("_", " ").title())

    if is_new_user:
        subject = f"You are invited to join {organization.name} on AuditAI Platform"
        text_body = (
            f"Hello {user.full_name},\n\n"
            f"{inviter.full_name} invited you to join {organization.name} on AuditAI Platform "
            f"as {role_label}.\n\n"
            f"Set your password and activate your account:\n{invite_link}\n\n"
            f"This link expires in {settings.invite_token_expire_days} days.\n\n"
            "If you did not expect this invitation, you can ignore this email."
        )
        html_body = (
            f"<p>Hello {user.full_name},</p>"
            f"<p><strong>{inviter.full_name}</strong> invited you to join "
            f"<strong>{organization.name}</strong> on AuditAI Platform as "
            f"<strong>{role_label}</strong>.</p>"
            f'<p><a href="{invite_link}">Set your password and join</a></p>'
            f"<p>This link expires in {settings.invite_token_expire_days} days.</p>"
            f"<p>If you did not expect this invitation, you can ignore this email.</p>"
        )
    else:
        subject = f"You are invited to join {organization.name} on AuditAI Platform"
        login_link = f"{settings.frontend_url.rstrip('/')}/?email={user.email}"
        text_body = (
            f"Hello {user.full_name},\n\n"
            f"{inviter.full_name} invited you to join {organization.name} on AuditAI Platform "
            f"as {role_label}.\n\n"
            f"Accept the invitation:\n{invite_link}\n\n"
            f"Or sign in with your existing password:\n{login_link}\n\n"
            f"This link expires in {settings.invite_token_expire_days} days."
        )
        html_body = (
            f"<p>Hello {user.full_name},</p>"
            f"<p><strong>{inviter.full_name}</strong> invited you to join "
            f"<strong>{organization.name}</strong> as <strong>{role_label}</strong>.</p>"
            f'<p><a href="{invite_link}">Accept invitation</a></p>'
            f'<p>Or <a href="{login_link}">sign in</a> with your existing password.</p>'
            f"<p>This link expires in {settings.invite_token_expire_days} days.</p>"
        )

    delivery = send_email(
        to=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )

    if delivery.sent:
        return InviteEmailResult(sent=True)

    if delivery.logged_to_console:
        logger.info("Invite link for %s: %s", user.email, invite_link)
        return InviteEmailResult(sent=False, invite_link=invite_link)

    return InviteEmailResult(sent=False, error=delivery.error)


def _load_invited_member(db: Session, payload: dict) -> OrganizationMember:
    try:
        member_id = uuid.UUID(payload["member_id"])
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise ValueError("This invitation link is invalid or has expired.") from exc

    member = db.query(OrganizationMember).filter(OrganizationMember.id == member_id).first()
    if not member or member.user_id != user_id:
        raise ValueError("This invitation is no longer valid.")
    if member.status != "invited":
        raise ValueError("This invitation has already been accepted or revoked.")
    return member
