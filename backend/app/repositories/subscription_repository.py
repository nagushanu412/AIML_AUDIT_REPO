from __future__ import annotations

import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.audit import (
    AuditEngagement,
    AuditProject,
    Client,
    OrganizationMember,
    OrganizationSubscription,
    Report,
    SubscriptionPlan,
)
from app.services.member_constants import ACTIVE_MEMBER_STATUSES
from app.services.subscription_constants import ACTIVE_SUBSCRIPTION_STATUSES


class SubscriptionRepository:
    def list_active_plans(self, db: Session) -> list[SubscriptionPlan]:
        return (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.display_order)
            .all()
        )

    def get_plan_by_code(self, db: Session, code: str) -> SubscriptionPlan | None:
        return (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.code == code, SubscriptionPlan.is_active.is_(True))
            .first()
        )

    def get_plan_by_id(self, db: Session, plan_id: uuid.UUID) -> SubscriptionPlan | None:
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()

    def get_active_subscription(
        self, db: Session, organization_id: uuid.UUID
    ) -> OrganizationSubscription | None:
        return (
            db.query(OrganizationSubscription)
            .options(joinedload(OrganizationSubscription.plan))
            .filter(
                OrganizationSubscription.organization_id == organization_id,
                OrganizationSubscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
            )
            .order_by(OrganizationSubscription.created_at.desc())
            .first()
        )

    def create_subscription(
        self, db: Session, subscription: OrganizationSubscription
    ) -> OrganizationSubscription:
        db.add(subscription)
        db.flush()
        return subscription

    def save_subscription(
        self, db: Session, subscription: OrganizationSubscription
    ) -> OrganizationSubscription:
        db.add(subscription)
        db.flush()
        return subscription

    def count_org_users(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .count()
        )

    def count_org_clients(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(Client)
            .filter(Client.organization_id == organization_id)
            .count()
        )

    def count_org_engagements(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(AuditEngagement)
            .filter(AuditEngagement.organization_id == organization_id)
            .count()
        )

    def count_org_reports(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(Report)
            .join(AuditProject, Report.project_id == AuditProject.id)
            .join(AuditEngagement, AuditProject.engagement_id == AuditEngagement.id)
            .join(Client, AuditEngagement.client_id == Client.id)
            .filter(Client.organization_id == organization_id)
            .count()
        )
