"""Plugin configuration seed for built modules."""

from __future__ import annotations

from app.services.findings_service import FINDING_TEMPLATES
from app.services.procurement_constants import (
    PROCUREMENT_REQUIRED_COLUMNS,
    PROCUREMENT_RULE_DEFINITIONS,
    PROCUREMENT_RULE_PREFIX,
)
from app.services.revenue_constants import (
    REVENUE_REQUIRED_COLUMNS,
    REVENUE_RULE_DEFINITIONS,
    REVENUE_RULE_PREFIX,
)

JOURNAL_RULE_CODES = [
    "LARGE_VALUE",
    "YEAR_END",
    "ROUND_AMOUNT",
    "WEEKEND",
    "SUSPENSE_ACCOUNT",
    "MANUAL_JOURNAL",
    "UNUSUAL_POSTING",
]

PLUGIN_CONFIG_SEED: list[dict] = [
    {
        "module_code": "JOURNAL_ENTRY_TESTING",
        "version": "1.0.0",
        "config": {
            "input_schema": {
                "format": "xlsx",
                "required_columns": [
                    "Date",
                    "Account",
                    "Debit",
                    "Credit",
                    "Description",
                ],
            },
            "validation": {"min_rows": 1},
            "rule_codes": JOURNAL_RULE_CODES,
            "finding_templates": FINDING_TEMPLATES,
            "report_types": [
                "journal_audit_summary",
                "journal_audit_excel",
                "journal_audit_pdf",
            ],
            "kpi_cards": ["high_risk_entries", "total_violations"],
            "risk_thresholds": {"high": 40, "medium": 20},
            "ui_config": {"stepper_steps": 6, "accent": "blue"},
        },
    },
    {
        "module_code": "REVENUE_TESTING",
        "version": "1.0.0",
        "config": {
            "input_schema": {
                "format": "xlsx",
                "required_columns": REVENUE_REQUIRED_COLUMNS,
            },
            "validation": {"min_rows": 1},
            "rule_codes": list(REVENUE_RULE_DEFINITIONS.keys()),
            "rule_prefix": REVENUE_RULE_PREFIX,
            "finding_templates": {},
            "report_types": [
                "revenue_audit_excel",
                "revenue_audit_pdf",
                "revenue_working_paper",
            ],
            "kpi_cards": ["high_risk_invoices", "gst_mismatch_count"],
            "risk_thresholds": {"high": 40, "medium": 20},
            "ui_config": {"stepper_steps": 6, "accent": "indigo"},
        },
    },
    {
        "module_code": "PROCUREMENT_TESTING",
        "version": "1.0.0",
        "config": {
            "input_schema": {
                "format": "xlsx",
                "required_columns": PROCUREMENT_REQUIRED_COLUMNS,
            },
            "validation": {"min_rows": 1},
            "rule_codes": list(PROCUREMENT_RULE_DEFINITIONS.keys()),
            "rule_prefix": PROCUREMENT_RULE_PREFIX,
            "finding_templates": {},
            "report_types": [
                "procurement_audit_excel",
                "procurement_audit_pdf",
                "procurement_working_paper",
            ],
            "kpi_cards": ["duplicate_payments", "missing_po_count"],
            "risk_thresholds": {"high": 40, "medium": 20},
            "ui_config": {"stepper_steps": 6, "accent": "emerald"},
        },
    },
]
