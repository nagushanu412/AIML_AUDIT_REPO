from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import OrganizationMember, User
from app.repositories.member_repository import MemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.auth_service import hash_password
from app.services.member_constants import (
    ACTIVE_MEMBER_STATUSES,
    INVITABLE_ROLES,
    MEMBER_ROLES,
    MEMBER_STATUSES,
    role_has_permission,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class InviteMemberResult:
    member: OrganizationMember
    is_new_user: bool


class MemberService:
    def __init__(
        self,
        repository: MemberRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        subscription_repository: SubscriptionRepository | None = None,
    ) -> None:
        self._repo = repository or MemberRepository()
        self._org_repo = organization_repository or OrganizationRepository()
        self._subscription_repo = subscription_repository or SubscriptionRepository()

    def create_owner_membership(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user: User,
        *,
        commit: bool = False,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user.id,
            role="organization_owner",
            status="active",
            joined_at=_now(),
        )
        self._repo.create(db, member)
        if commit:
            db.commit()
            db.refresh(member)
        return member

    def get_caller_membership(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> OrganizationMember:
        membership = self._repo.get_membership(db, organization_id, user.id)
        if not membership or membership.status not in ACTIVE_MEMBER_STATUSES:
            raise PermissionError("You do not have access to this organization.")
        return membership

    def assert_permission(
        self, db: Session, user: User, organization_id: uuid.UUID, permission: str
    ) -> OrganizationMember:
        membership = self.get_caller_membership(db, user, organization_id)
        if not role_has_permission(membership.role, permission):
            raise PermissionError("You do not have permission for this action.")
        return membership

    def list_members(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> list[OrganizationMember]:
        self.assert_permission(db, user, organization_id, "members.list")
        return self._repo.list_by_organization(db, organization_id)

    def invite_member(
        self,
        db: Session,
        user: User,
        organization_id: uuid.UUID,
        *,
        email: str,
        role: str,
        full_name: str | None = None,
    ) -> InviteMemberResult:
        self.assert_permission(db, user, organization_id, "members.invite")
        self._validate_role(role, allow_owner=False)
        self._assert_user_capacity(db, organization_id)

        normalized_email = email.strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise ValueError("A valid email address is required.")

        target_user = self._repo.get_user_by_email(db, normalized_email)
        now = _now()
        is_new_user = target_user is None

        if target_user:
            member = self._invite_existing_user(
                db, organization_id, target_user, role=role, invited_at=now
            )
        else:
            member = self._invite_new_user(
                db,
                organization_id,
                email=normalized_email,
                role=role,
                full_name=full_name or normalized_email.split("@")[0],
                invited_at=now,
            )

        db.commit()
        refreshed = self._repo.get_by_id(db, member.id)
        return InviteMemberResult(
            member=refreshed or member,
            is_new_user=is_new_user,
        )

    def update_member(
        self,
        db: Session,
        user: User,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
        *,
        role: str | None = None,
        status: str | None = None,
    ) -> OrganizationMember:
        self.assert_permission(db, user, organization_id, "members.update")

        member = self._repo.get_by_id(db, member_id)
        if not member or member.organization_id != organization_id:
            raise ValueError("Member not found.")

        caller = self.get_caller_membership(db, user, organization_id)

        if role is not None:
            self._validate_role(role, allow_owner=caller.role == "organization_owner")
            if member.role == "organization_owner" and role != "organization_owner":
                if self._repo.count_active_owners(db, organization_id) <= 1:
                    raise ValueError("Cannot change role of the only organization owner.")
            if role == "organization_owner" and caller.role != "organization_owner":
                raise PermissionError("Only an organization owner can assign the owner role.")
            member.role = role

        if status is not None:
            self._validate_status(status)
            if member.role == "organization_owner" and status == "disabled":
                if self._repo.count_active_owners(db, organization_id) <= 1:
                    raise ValueError("Cannot disable the only organization owner.")
            if member.status == "invited" and status == "active" and not member.joined_at:
                member.joined_at = _now()
            member.status = status

        self._repo.save(db, member)
        db.commit()
        refreshed = self._repo.get_by_id(db, member.id)
        return refreshed or member

    def remove_member(
        self,
        db: Session,
        user: User,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> OrganizationMember:
        self.assert_permission(db, user, organization_id, "members.remove")

        member = self._repo.get_by_id(db, member_id)
        if not member or member.organization_id != organization_id:
            raise ValueError("Member not found.")

        if member.user_id == user.id:
            raise ValueError("You cannot remove yourself. Ask another admin.")

        if member.role == "organization_owner":
            if self._repo.count_active_owners(db, organization_id) <= 1:
                raise ValueError("Cannot remove the only organization owner.")

        member.status = "disabled"
        self._repo.save(db, member)

        if member.user and member.user.default_organization_id == organization_id:
            self._org_repo.clear_user_default_organization(db, member.user)

        db.commit()
        refreshed = self._repo.get_by_id(db, member.id)
        return refreshed or member

    def activate_invited_memberships(self, db: Session, user: User) -> None:
        memberships = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == user.id,
                OrganizationMember.status == "invited",
            )
            .all()
        )
        if not memberships:
            return

        now = _now()
        for membership in memberships:
            membership.status = "active"
            if not membership.joined_at:
                membership.joined_at = now

        db.commit()

    def resolve_user_organization_id(
        self, db: Session, user: User
    ) -> uuid.UUID | None:
        if user.default_organization_id:
            membership = self._repo.get_membership(
                db, user.default_organization_id, user.id
            )
            if membership and membership.status in ACTIVE_MEMBER_STATUSES:
                return user.default_organization_id

        membership = self._repo.get_active_membership_for_user(db, user.id)
        if membership:
            if user.default_organization_id != membership.organization_id:
                self._org_repo.link_user_default_organization(
                    db, user, membership.organization_id
                )
                db.commit()
            return membership.organization_id

        return user.default_organization_id

    def user_can_access_organization(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> bool:
        membership = self._repo.get_membership(db, organization_id, user.id)
        if membership and membership.status in ACTIVE_MEMBER_STATUSES:
            return True
        return user.default_organization_id == organization_id

    def user_has_active_membership(self, db: Session, user_id: uuid.UUID) -> bool:
        return self._repo.user_has_active_membership(db, user_id)

    def _invite_existing_user(
        self,
        db: Session,
        organization_id: uuid.UUID,
        target_user: User,
        *,
        role: str,
        invited_at: datetime,
    ) -> OrganizationMember:
        existing = self._repo.get_membership(db, organization_id, target_user.id)
        if existing and existing.status in ACTIVE_MEMBER_STATUSES:
            raise ValueError("This user is already a member of your organization.")

        if target_user.default_organization_id and target_user.default_organization_id != organization_id:
            other = self._repo.get_membership(
                db, target_user.default_organization_id, target_user.id
            )
            if other and other.status in ACTIVE_MEMBER_STATUSES:
                raise ValueError(
                    "This user already belongs to another organization. "
                    "Multi-organization membership is not supported in Phase 1."
                )

        if existing:
            existing.role = role
            existing.status = "invited"
            existing.invited_at = invited_at
            member = existing
        else:
            member = OrganizationMember(
                organization_id=organization_id,
                user_id=target_user.id,
                role=role,
                status="invited",
                invited_at=invited_at,
            )
            self._repo.create(db, member)

        if not target_user.default_organization_id:
            self._org_repo.link_user_default_organization(db, target_user, organization_id)

        return member

    def _invite_new_user(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        email: str,
        role: str,
        full_name: str,
        invited_at: datetime,
    ) -> OrganizationMember:
        temp_password = secrets.token_urlsafe(32)
        new_user = User(
            email=email,
            password_hash=hash_password(temp_password),
            full_name=full_name.strip() or email.split("@")[0],
            role="auditor",
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        member = OrganizationMember(
            organization_id=organization_id,
            user_id=new_user.id,
            role=role,
            status="invited",
            invited_at=invited_at,
        )
        self._repo.create(db, member)
        self._org_repo.link_user_default_organization(db, new_user, organization_id)
        return member

    def _assert_user_capacity(self, db: Session, organization_id: uuid.UUID) -> None:
        from app.services.subscription_enforcement import SubscriptionEnforcementService

        SubscriptionEnforcementService().assert_can_add_user(db, organization_id)

    @staticmethod
    def _validate_role(role: str, *, allow_owner: bool) -> None:
        normalized = role.strip().lower()
        allowed = MEMBER_ROLES if allow_owner else INVITABLE_ROLES
        if normalized not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            raise ValueError(f"Invalid role. Allowed values: {allowed_list}.")

    @staticmethod
    def _validate_status(status: str) -> None:
        normalized = status.strip().lower()
        if normalized not in MEMBER_STATUSES:
            allowed = ", ".join(sorted(MEMBER_STATUSES))
            raise ValueError(f"Invalid status. Allowed values: {allowed}.")
