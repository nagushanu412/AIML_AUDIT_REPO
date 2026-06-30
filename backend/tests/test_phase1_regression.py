"""Phase 1 regression and tenant isolation tests (Milestone 10)."""

from app.services.module_catalog_constants import MODULE_CATALOG_SEED
from app.services.subscription_enforcement import SubscriptionEnforcementService
from app.services.subscription_service import SubscriptionService


def test_phase1_catalog_count():
    assert len(MODULE_CATALOG_SEED) == 22


def test_subscription_enforcement_service_exists():
    service = SubscriptionEnforcementService()
    assert hasattr(service, "assert_can_add_client")


def test_subscription_limit_check_regression():
    service = SubscriptionService()
    assert service.check_limit("clients", 5, 10) is True
    assert service.check_limit("clients", 10, 10) is False
