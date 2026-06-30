"""Backfill organization_id and membership for existing tenant data (Milestone 9).

Run: python -m scripts.backfill_tenant_data
"""
from __future__ import annotations

from app.database import SessionLocal
from app.models.audit import AuditEngagement, Client, Organization, OrganizationMember, User
from app.services.member_constants import ACTIVE_MEMBER_STATUSES
from app.services.organization_service import OrganizationService


def backfill(db) -> dict[str, int]:
    stats = {
        "organizations_created": 0,
        "members_created": 0,
        "clients_updated": 0,
        "engagements_updated": 0,
    }
    org_service = OrganizationService()

    users_without_org = (
        db.query(User)
        .outerjoin(
            OrganizationMember,
            (OrganizationMember.user_id == User.id)
            & OrganizationMember.status.in_(ACTIVE_MEMBER_STATUSES),
        )
        .filter(OrganizationMember.id.is_(None))
        .all()
    )

    for user in users_without_org:
        if user.default_organization_id:
            continue
        name = (user.company_name or user.full_name or user.email.split("@")[0]).strip()
        if len(name) < 2:
            name = f"Firm of {user.full_name}"
        try:
            org_service.create_organization(db, user, name=name)
            stats["organizations_created"] += 1
            stats["members_created"] += 1
        except ValueError:
            continue

    db.commit()

    clients = db.query(Client).filter(Client.organization_id.is_(None)).all()
    for client in clients:
        user = db.query(User).filter(User.id == client.user_id).first()
        if user and user.default_organization_id:
            client.organization_id = user.default_organization_id
            stats["clients_updated"] += 1

    engagements = (
        db.query(AuditEngagement).filter(AuditEngagement.organization_id.is_(None)).all()
    )
    for engagement in engagements:
        client = db.query(Client).filter(Client.id == engagement.client_id).first()
        if client and client.organization_id:
            engagement.organization_id = client.organization_id
            stats["engagements_updated"] += 1

    db.commit()
    return stats


def main() -> None:
    db = SessionLocal()
    try:
        result = backfill(db)
        print("Backfill complete:", result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
