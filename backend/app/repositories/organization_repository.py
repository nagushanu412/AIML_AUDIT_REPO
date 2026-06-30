from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import Organization, User


class OrganizationRepository:
    def get_by_id(self, db: Session, organization_id: uuid.UUID) -> Organization | None:
        return db.query(Organization).filter(Organization.id == organization_id).first()

    def get_by_slug(self, db: Session, slug: str) -> Organization | None:
        return db.query(Organization).filter(Organization.slug == slug).first()

    def slug_exists(self, db: Session, slug: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        query = db.query(Organization.id).filter(Organization.slug == slug)
        if exclude_id is not None:
            query = query.filter(Organization.id != exclude_id)
        return query.first() is not None

    def create(self, db: Session, organization: Organization) -> Organization:
        db.add(organization)
        db.flush()
        return organization

    def save(self, db: Session, organization: Organization) -> Organization:
        db.add(organization)
        db.flush()
        return organization

    def link_user_default_organization(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> User:
        user.default_organization_id = organization_id
        db.add(user)
        db.flush()
        return user

    def clear_user_default_organization(self, db: Session, user: User) -> User:
        user.default_organization_id = None
        db.add(user)
        db.flush()
        return user
