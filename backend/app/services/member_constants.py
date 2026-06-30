from __future__ import annotations

MEMBER_ROLES = frozenset(
    {
        "organization_owner",
        "partner",
        "audit_manager",
        "senior_auditor",
        "auditor",
        "reviewer",
        "client_user",
        "read_only",
    }
)

INVITABLE_ROLES = frozenset(MEMBER_ROLES - {"organization_owner"})

MEMBER_STATUSES = frozenset({"active", "invited", "disabled"})

ACTIVE_MEMBER_STATUSES = frozenset({"active", "invited"})

ROLE_LABELS: dict[str, str] = {
    "organization_owner": "Organization Owner",
    "partner": "Partner",
    "audit_manager": "Audit Manager",
    "senior_auditor": "Senior Auditor",
    "auditor": "Auditor",
    "reviewer": "Reviewer",
    "client_user": "Client User",
    "read_only": "Read Only",
}

# RBAC foundation — expanded in Milestone 4 (tenant isolation) and Milestone 8.
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "organization_owner": frozenset(
        {
            "members.list",
            "members.invite",
            "members.update",
            "members.remove",
            "organization.update",
            "organization.close",
            "subscription.change",
        }
    ),
    "partner": frozenset({"members.list", "organization.update"}),
    "audit_manager": frozenset(
        {
            "members.list",
            "members.invite",
            "members.update",
            "members.remove",
            "organization.update",
        }
    ),
    "senior_auditor": frozenset({"members.list"}),
    "auditor": frozenset({"members.list"}),
    "reviewer": frozenset({"members.list"}),
    "client_user": frozenset(),
    "read_only": frozenset(),
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
