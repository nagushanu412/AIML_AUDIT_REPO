from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import OrganizationSubscription, SubscriptionPlan, User
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.member_service import MemberService
from app.services.subscription_constants import (
    DEFAULT_PLAN_CODE,
    PLAN_CODES,
)


def _plan_to_dict(plan: SubscriptionPlan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "description": plan.description,
        "max_users": plan.max_users,
        "max_clients": plan.max_clients,
        "max_engagements": plan.max_engagements,
        "max_storage_bytes": plan.max_storage_bytes,
        "monthly_ai_credits": plan.monthly_ai_credits,
        "monthly_uploads": plan.monthly_uploads,
        "max_reports": plan.max_reports,
        "enabled_module_codes": plan.enabled_module_codes,
        "api_rate_limit": plan.api_rate_limit,
        "support_level": plan.support_level,
        "display_order": plan.display_order,
        "is_active": plan.is_active,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


class SubscriptionService:
    def __init__(
        self,
        repository: SubscriptionRepository | None = None,
        member_service: MemberService | None = None,
    ) -> None:
        self._repo = repository or SubscriptionRepository()
        self._member_service = member_service or MemberService()

    def list_plans(self, db: Session) -> list[SubscriptionPlan]:
        return self._repo.list_active_plans(db)

    def assign_default_plan(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        plan_code: str = DEFAULT_PLAN_CODE,
        commit: bool = True,
    ) -> OrganizationSubscription:
        existing = self._repo.get_active_subscription(db, organization_id)
        if existing:
            return existing

        plan = self._repo.get_plan_by_code(db, plan_code)
        if not plan:
            raise ValueError(f"Subscription plan '{plan_code}' not found.")

        subscription = OrganizationSubscription(
            organization_id=organization_id,
            subscription_plan_id=plan.id,
            status="active",
            started_at=datetime.now(timezone.utc),
        )
        self._repo.create_subscription(db, subscription)
        if commit:
            db.commit()
            db.refresh(subscription)
        else:
            db.flush()
        return subscription

    def get_organization_subscription(
        self, db: Session, user: User
    ) -> OrganizationSubscription | None:
        if not user.default_organization_id:
            return None
        return self._repo.get_active_subscription(db, user.default_organization_id)

    def get_subscription_summary(self, db: Session, user: User) -> dict[str, Any]:
        org_id = self._member_service.resolve_user_organization_id(db, user)
        if not org_id:
            raise ValueError("No organization linked to this account.")

        subscription = self._repo.get_active_subscription(db, org_id)
        if not subscription or not subscription.plan:
            raise ValueError("No active subscription for this organization.")

        usage = {
            "users": self._repo.count_org_users(db, org_id),
            "clients": self._repo.count_org_clients(db, org_id),
            "engagements": self._repo.count_org_engagements(db, org_id),
            "reports": self._repo.count_org_reports(db, org_id),
            "uploads": 0,
            "storage_bytes": 0,
            "ai_credits": 0,
        }
        plan = subscription.plan
        limits = {
            "max_users": plan.max_users,
            "max_clients": plan.max_clients,
            "max_engagements": plan.max_engagements,
            "max_reports": plan.max_reports,
            "monthly_uploads": plan.monthly_uploads,
            "max_storage_bytes": plan.max_storage_bytes,
            "monthly_ai_credits": plan.monthly_ai_credits,
            "api_rate_limit": plan.api_rate_limit,
        }

        return {
            "subscription": {
                "id": subscription.id,
                "organization_id": subscription.organization_id,
                "status": subscription.status,
                "started_at": subscription.started_at,
                "ends_at": subscription.ends_at,
            },
            "plan": _plan_to_dict(plan),
            "usage": usage,
            "limits": limits,
        }

    def change_plan(
        self, db: Session, user: User, *, plan_code: str
    ) -> OrganizationSubscription:
        org_id = self._member_service.resolve_user_organization_id(db, user)
        if not org_id:
            raise ValueError("No organization linked to this account.")

        self._member_service.assert_permission(db, user, org_id, "subscription.change")

        normalized = plan_code.strip().lower()
        if normalized not in PLAN_CODES:
            raise ValueError(
                f"Invalid plan code. Allowed: {', '.join(sorted(PLAN_CODES))}."
            )

        new_plan = self._repo.get_plan_by_code(db, normalized)
        if not new_plan:
            raise ValueError(f"Plan '{normalized}' is not available.")

        current = self._repo.get_active_subscription(db, org_id)
        if current and current.subscription_plan_id == new_plan.id:
            return current

        now = datetime.now(timezone.utc)
        if current:
            current.status = "cancelled"
            current.ends_at = now
            self._repo.save_subscription(db, current)

        subscription = OrganizationSubscription(
            organization_id=org_id,
            subscription_plan_id=new_plan.id,
            status="active",
            started_at=now,
        )
        self._repo.create_subscription(db, subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    def check_limit(
        self,
        metric: str,
        usage_value: int,
        limit_value: int,
    ) -> bool:
        """Return True if usage is within limit."""
        if limit_value <= 0:
            return True
        return usage_value < limit_value
