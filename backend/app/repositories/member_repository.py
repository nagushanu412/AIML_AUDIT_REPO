from __future__ import annotations

import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.audit import OrganizationMember, User
from app.services.member_constants import ACTIVE_MEMBER_STATUSES


class MemberRepository:
    def get_by_id(
        self, db: Session, member_id: uuid.UUID
    ) -> OrganizationMember | None:
        return (
            db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .filter(OrganizationMember.id == member_id)
            .first()
        )

    def get_membership(
        self, db: Session, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMember | None:
        return (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
            .first()
        )

    def get_active_membership_for_user(
        self, db: Session, user_id: uuid.UUID
    ) -> OrganizationMember | None:
        return (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == user_id,
                OrganizationMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .order_by(OrganizationMember.created_at.asc())
            .first()
        )

    def user_has_active_membership(self, db: Session, user_id: uuid.UUID) -> bool:
        return self.get_active_membership_for_user(db, user_id) is not None

    def list_by_organization(
        self, db: Session, organization_id: uuid.UUID
    ) -> list[OrganizationMember]:
        return (
            db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .filter(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at.asc())
            .all()
        )

    def count_active_members(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .count()
        )

    def count_active_owners(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == "organization_owner",
                OrganizationMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .count()
        )

    def create(self, db: Session, member: OrganizationMember) -> OrganizationMember:
        db.add(member)
        db.flush()
        return member

    def save(self, db: Session, member: OrganizationMember) -> OrganizationMember:
        db.add(member)
        db.flush()
        return member

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        normalized = email.strip().lower()
        return db.query(User).filter(User.email == normalized).first()
