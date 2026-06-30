from __future__ import annotations

ENGAGEMENT_TEAM_ROLES = frozenset(
    {
        "partner",
        "audit_manager",
        "senior_auditor",
        "auditor",
        "reviewer",
    }
)

ENGAGEMENT_SINGLE_SLOT_ROLES = frozenset({"partner", "audit_manager"})

ENGAGEMENT_TEAM_STATUSES = frozenset({"active", "removed"})

ACTIVE_TEAM_STATUSES = frozenset({"active"})

HISTORY_ACTIONS = frozenset({"assigned", "role_changed", "removed", "reactivated"})

ENGAGEMENT_TEAM_ROLE_LABELS: dict[str, str] = {
    "partner": "Engagement Partner",
    "audit_manager": "Audit Manager",
    "senior_auditor": "Senior Auditor",
    "auditor": "Auditor",
    "reviewer": "Reviewer",
}

# Org roles allowed to manage engagement team assignments.
ENGAGEMENT_TEAM_MANAGE_ORG_ROLES = frozenset(
    {"organization_owner", "partner", "audit_manager"}
)

# Minimum organization role required to hold an engagement team role.
ENGAGEMENT_ROLE_MIN_ORG_ROLE: dict[str, frozenset[str]] = {
    "partner": frozenset({"organization_owner", "partner"}),
    "audit_manager": frozenset({"organization_owner", "partner", "audit_manager"}),
    "senior_auditor": frozenset(
        {
            "organization_owner",
            "partner",
            "audit_manager",
            "senior_auditor",
        }
    ),
    "auditor": frozenset(
        {
            "organization_owner",
            "partner",
            "audit_manager",
            "senior_auditor",
            "auditor",
        }
    ),
    "reviewer": frozenset(
        {
            "organization_owner",
            "partner",
            "audit_manager",
            "senior_auditor",
            "auditor",
            "reviewer",
        }
    ),
}

EXCLUDED_ORG_ROLES_FOR_TEAM = frozenset({"client_user", "read_only"})

# Engagement-level permissions (foundation for later milestones).
ENGAGEMENT_TEAM_PERMISSIONS: dict[str, frozenset[str]] = {
    "partner": frozenset(
        {
            "team.view",
            "team.manage",
            "engagement.approve",
            "findings.approve",
            "reports.approve",
            "modules.view",
        }
    ),
    "audit_manager": frozenset(
        {
            "team.view",
            "team.manage",
            "engagement.manage",
            "findings.review",
            "modules.manage",
            "modules.view",
        }
    ),
    "senior_auditor": frozenset(
        {
            "team.view",
            "findings.review",
            "modules.view",
            "evidence.upload",
            "workpapers.manage",
        }
    ),
    "auditor": frozenset(
        {
            "team.view",
            "modules.view",
            "evidence.upload",
            "workpapers.manage",
            "findings.create",
        }
    ),
    "reviewer": frozenset(
        {
            "team.view",
            "findings.review",
            "modules.view",
        }
    ),
}


def engagement_role_has_permission(role: str, permission: str) -> bool:
    return permission in ENGAGEMENT_TEAM_PERMISSIONS.get(role, frozenset())
