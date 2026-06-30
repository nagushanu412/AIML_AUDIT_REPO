"""Unit tests for subscription helpers."""

from __future__ import annotations

from app.services.subscription_constants import DEFAULT_PLAN_CODE, PLAN_CODES
from app.services.subscription_service import SubscriptionService


def test_plan_codes_include_four_tiers():
    assert PLAN_CODES == frozenset({"free", "starter", "professional", "enterprise"})


def test_default_plan_is_free():
    assert DEFAULT_PLAN_CODE == "free"


def test_check_limit_within():
    service = SubscriptionService()
    assert service.check_limit("clients", 5, 10) is True


def test_check_limit_at_cap():
    service = SubscriptionService()
    assert service.check_limit("clients", 10, 10) is False


def test_check_limit_unlimited_style():
    service = SubscriptionService()
    assert service.check_limit("clients", 100, 99999) is True
