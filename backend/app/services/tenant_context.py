from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.audit import User
from app.repositories.member_repository import MemberRepository
from app.services.member_constants import ACTIVE_MEMBER_STATUSES


@dataclass(frozen=True)
class TenantContext:
    user: User
    organization_id: uuid.UUID | None
    member_role: str | None


class TenantContextService:
    def __init__(self, member_repository: MemberRepository | None = None) -> None:
        self._member_repo = member_repository or MemberRepository()

    def resolve_for_user(self, db: Session, user: User) -> TenantContext:
        org_id: uuid.UUID | None = None
        member_role: str | None = None

        if user.default_organization_id:
            membership = self._member_repo.get_membership(
                db, user.default_organization_id, user.id
            )
            if membership and membership.status in ACTIVE_MEMBER_STATUSES:
                org_id = user.default_organization_id
                member_role = membership.role

        if org_id is None:
            membership = self._member_repo.get_active_membership_for_user(db, user.id)
            if membership:
                org_id = membership.organization_id
                member_role = membership.role

        return TenantContext(
            user=user,
            organization_id=org_id,
            member_role=member_role,
        )

    def validate_token_org_claims(
        self,
        db: Session,
        user: User,
        *,
        token_org_id: uuid.UUID | None,
        token_org_role: str | None,
    ) -> TenantContext:
        resolved = self.resolve_for_user(db, user)

        if token_org_id is not None:
            if resolved.organization_id is None:
                raise PermissionError("No organization linked to this account.")
            if token_org_id != resolved.organization_id:
                raise PermissionError("Organization context mismatch.")
            membership = self._member_repo.get_membership(db, token_org_id, user.id)
            if not membership or membership.status not in ACTIVE_MEMBER_STATUSES:
                raise PermissionError("You do not have access to this organization.")
            role = membership.role
            if token_org_role and token_org_role != membership.role:
                role = membership.role
            return TenantContext(
                user=user,
                organization_id=token_org_id,
                member_role=role,
            )

        return resolved
