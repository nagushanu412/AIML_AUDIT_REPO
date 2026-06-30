from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.subscription_repository import SubscriptionRepository
from app.services.subscription_service import SubscriptionService
from app.services.tenant_context import TenantContext


class SubscriptionEnforcementService:
    def __init__(self, repository: SubscriptionRepository | None = None) -> None:
        self._repo = repository or SubscriptionRepository()
        self._subscription_service = SubscriptionService(repository=self._repo)

    def assert_can_add_user(self, db: Session, organization_id: uuid.UUID) -> None:
        self._assert_limit(
            db,
            organization_id,
            metric="users",
            current=self._repo.count_org_users(db, organization_id),
            limit_field="max_users",
        )

    def assert_can_add_client(self, db: Session, tenant: TenantContext) -> None:
        if not tenant.organization_id:
            return
        self._assert_limit(
            db,
            tenant.organization_id,
            metric="clients",
            current=self._repo.count_org_clients(db, tenant.organization_id),
            limit_field="max_clients",
        )

    def assert_can_add_engagement(self, db: Session, tenant: TenantContext) -> None:
        if not tenant.organization_id:
            return
        self._assert_limit(
            db,
            tenant.organization_id,
            metric="engagements",
            current=self._repo.count_org_engagements(db, tenant.organization_id),
            limit_field="max_engagements",
        )

    def assert_can_add_report(self, db: Session, tenant: TenantContext) -> None:
        if not tenant.organization_id:
            return
        self._assert_limit(
            db,
            tenant.organization_id,
            metric="reports",
            current=self._repo.count_org_reports(db, tenant.organization_id),
            limit_field="max_reports",
        )

    def assert_module_allowed(
        self, db: Session, tenant: TenantContext, module_code: str
    ) -> None:
        if not tenant.organization_id:
            return
        subscription = self._repo.get_active_subscription(db, tenant.organization_id)
        if not subscription or not subscription.plan:
            return
        allowed = subscription.plan.enabled_module_codes or []
        if allowed and module_code not in allowed:
            raise ValueError(
                f"Module '{module_code}' is not included in your subscription plan."
            )

    def _assert_limit(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        metric: str,
        current: int,
        limit_field: str,
    ) -> None:
        subscription = self._repo.get_active_subscription(db, organization_id)
        if not subscription or not subscription.plan:
            return
        limit_value = getattr(subscription.plan, limit_field, 0)
        if not self._subscription_service.check_limit(metric, current, limit_value):
            raise ValueError(
                f"Subscription limit reached for {metric} ({current}/{limit_value}). "
                "Upgrade your plan to continue."
            )
