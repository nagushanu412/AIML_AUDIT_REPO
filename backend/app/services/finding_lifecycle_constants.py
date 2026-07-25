from __future__ import annotations

FINDING_STATUSES = frozenset({"open", "under_review", "cleared", "accepted", "closed"})

# Statuses that have not yet received an auditor decision stamp.
PRE_DECISION_STATUSES = frozenset({"open", "under_review"})

REMEDIATION_STATUSES = frozenset({"not_started", "in_progress", "completed", "overdue"})

STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"under_review", "cleared", "accepted", "closed"}),
    "under_review": frozenset({"open", "cleared", "accepted", "closed"}),
    "cleared": frozenset({"closed", "open"}),
    "accepted": frozenset({"closed", "under_review"}),
    "closed": frozenset({"open"}),
}

FINDING_UPDATE_ROLES = frozenset(
    {"organization_owner", "partner", "audit_manager", "senior_auditor", "auditor", "reviewer"}
)

FINDING_APPROVE_ROLES = frozenset({"organization_owner", "partner", "audit_manager", "reviewer"})

FINDING_REOPEN_ROLES = frozenset({"organization_owner", "partner", "audit_manager"})
