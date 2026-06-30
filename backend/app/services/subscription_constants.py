"""Subscription plan codes and statuses."""

PLAN_CODES = frozenset({"free", "starter", "professional", "enterprise"})

DEFAULT_PLAN_CODE = "free"

ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"trialing", "active"})

SUBSCRIPTION_STATUSES = frozenset(
    {"trialing", "active", "past_due", "cancelled", "expired"}
)
