from __future__ import annotations

EVIDENCE_CATEGORIES = frozenset(
    {
        "invoice",
        "contract",
        "correspondence",
        "bank_statement",
        "screenshot",
        "spreadsheet",
        "report",
        "other",
    }
)

EVIDENCE_STATUSES = frozenset({"active", "archived"})

LINKED_ENTITY_TYPES = frozenset({"finding", "workpaper", "journal_entry", "transaction"})

LINK_TYPES = frozenset({"supports", "references", "attachment"})

EVIDENCE_MANAGE_ORG_ROLES = frozenset(
    {"organization_owner", "partner", "audit_manager", "senior_auditor", "auditor"}
)
