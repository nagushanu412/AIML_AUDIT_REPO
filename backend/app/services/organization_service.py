from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import Organization, User
from app.repositories.organization_repository import OrganizationRepository
from app.services.member_service import MemberService
from app.services.organization_constants import (
    DEFAULT_ORGANIZATION_STATUS,
    ORGANIZATION_STATUSES,
)

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_SLUG_LENGTH = 100


def slugify_name(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        slug = "organization"
    return slug[:_MAX_SLUG_LENGTH]


def generate_unique_slug(db: Session, repo: OrganizationRepository, name: str) -> str:
    base = slugify_name(name)
    candidate = base
    suffix = 2
    while repo.slug_exists(db, candidate):
        suffix_part = f"-{suffix}"
        candidate = f"{base[: _MAX_SLUG_LENGTH - len(suffix_part)]}{suffix_part}"
        suffix += 1
    return candidate


def validate_slug(slug: str) -> None:
    normalized = slug.strip().lower()
    if not normalized or len(normalized) > _MAX_SLUG_LENGTH:
        raise ValueError("Slug must be 1–100 characters.")
    if not _SLUG_PATTERN.match(normalized):
        raise ValueError(
            "Slug must contain only lowercase letters, numbers, and hyphens."
        )


def validate_status(status: str) -> None:
    if status not in ORGANIZATION_STATUSES:
        raise ValueError(
            f"Invalid status. Allowed values: {', '.join(sorted(ORGANIZATION_STATUSES))}."
        )


class OrganizationService:
    def __init__(
        self,
        repository: OrganizationRepository | None = None,
        member_service: MemberService | None = None,
    ) -> None:
        self._repo = repository or OrganizationRepository()
        self._member_service = member_service or MemberService()

    def get_user_organization(self, db: Session, user: User) -> Organization | None:
        org_id = self._member_service.resolve_user_organization_id(db, user)
        if not org_id:
            return None
        return self._repo.get_by_id(db, org_id)

    def get_organization_for_user(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> Organization:
        organization = self._assert_user_can_access(db, user, organization_id)
        if organization.status == "closed":
            raise ValueError("Organization is closed.")
        return organization

    def create_organization(
        self,
        db: Session,
        user: User,
        *,
        name: str,
        slug: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Organization:
        if user.default_organization_id:
            raise ValueError(
                "You already belong to an organization. "
                "Contact your firm admin if you need access to a different organization."
            )
        if self._member_service.user_has_active_membership(db, user.id):
            raise ValueError(
                "You already belong to an organization. "
                "Contact your firm admin if you need access to a different organization."
            )

        trimmed_name = name.strip()
        if len(trimmed_name) < 2:
            raise ValueError("Organization name must be at least 2 characters.")

        if slug is not None:
            validate_slug(slug)
            normalized_slug = slug.strip().lower()
            if self._repo.slug_exists(db, normalized_slug):
                raise ValueError("An organization with this slug already exists.")
        else:
            normalized_slug = generate_unique_slug(db, self._repo, trimmed_name)

        organization = Organization(
            name=trimmed_name,
            slug=normalized_slug,
            status=DEFAULT_ORGANIZATION_STATUS,
            settings=settings or {},
        )
        self._repo.create(db, organization)
        self._repo.link_user_default_organization(db, user, organization.id)
        self._member_service.create_owner_membership(
            db, organization.id, user, commit=False
        )
        from app.services.subscription_service import SubscriptionService

        SubscriptionService().assign_default_plan(
            db, organization.id, commit=False
        )
        db.commit()
        db.refresh(organization)
        return organization

    def update_organization(
        self,
        db: Session,
        user: User,
        organization_id: uuid.UUID,
        *,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Organization:
        organization = self._assert_user_can_access(db, user, organization_id)
        self._member_service.assert_permission(
            db, user, organization_id, "organization.update"
        )

        if name is not None:
            trimmed_name = name.strip()
            if len(trimmed_name) < 2:
                raise ValueError("Organization name must be at least 2 characters.")
            organization.name = trimmed_name

        if slug is not None:
            validate_slug(slug)
            normalized_slug = slug.strip().lower()
            if self._repo.slug_exists(db, normalized_slug, exclude_id=organization.id):
                raise ValueError("An organization with this slug already exists.")
            organization.slug = normalized_slug

        if status is not None:
            validate_status(status)
            organization.status = status

        if settings is not None:
            organization.settings = settings

        self._repo.save(db, organization)
        db.commit()
        db.refresh(organization)
        return organization

    def close_organization(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> Organization:
        organization = self._assert_user_can_access(db, user, organization_id)
        self._member_service.assert_permission(
            db, user, organization_id, "organization.close"
        )
        organization.status = "closed"
        self._repo.clear_user_default_organization(db, user)
        db.commit()
        db.refresh(organization)
        return organization

    def _assert_user_can_access(
        self, db: Session, user: User, organization_id: uuid.UUID
    ) -> Organization:
        if not self._member_service.user_can_access_organization(
            db, user, organization_id
        ):
            raise PermissionError("You do not have access to this organization.")
        organization = self._repo.get_by_id(db, organization_id)
        if not organization:
            raise ValueError("Organization not found.")
        return organization
