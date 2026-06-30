from __future__ import annotations

WORKPAPER_CATEGORIES = frozenset(
    {
        "planning",
        "risk_assessment",
        "testing",
        "sampling",
        "completion",
        "other",
    }
)

WORKPAPER_STATUSES = frozenset({"draft", "final", "archived"})

WORKPAPER_MANAGE_ORG_ROLES = frozenset(
    {"organization_owner", "partner", "audit_manager", "senior_auditor", "auditor"}
)
