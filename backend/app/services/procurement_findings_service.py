from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, ProcurementRuleResult, RuleMaster


PROCUREMENT_FINDING_TEMPLATES: dict[str, dict] = {
    "PROC_DUPLICATE_PAYMENT": {
        "title": "Duplicate vendor payments identified",
        "observation": "Same vendor and invoice number combination appears more than once.",
        "impact": "Risk of duplicate payment and overstated expenses.",
        "recommendation": "Verify payment vouchers and cancel duplicate entries.",
    },
    "PROC_MISSING_PO": {
        "title": "Invoices without purchase order reference",
        "observation": "High-value vendor invoices lack PO linkage.",
        "impact": "Weak three-way match controls and unauthorized procurement risk.",
        "recommendation": "Obtain PO approval evidence and perform three-way matching.",
    },
    "PROC_GST_MISMATCH": {
        "title": "GST input tax mismatches on vendor invoices",
        "observation": "GST amount inconsistent with taxable value at standard rates.",
        "impact": "Input tax credit and expense accuracy may be misstated.",
        "recommendation": "Reconcile with GSTR-2B and validate vendor invoices.",
    },
    "PROC_HIGH_VALUE": {
        "title": "High-value vendor invoices flagged",
        "observation": "Vendor invoices exceed the engagement large-value threshold.",
        "impact": "Material payables require enhanced substantive procedures.",
        "recommendation": "Obtain PO, GRN, and payment support for sample items.",
    },
    "PROC_ROUND_AMOUNT": {
        "title": "Round-figure vendor invoices detected",
        "observation": "Vendor invoice totals are round amounts.",
        "impact": "May indicate estimates or manual billing adjustments.",
        "recommendation": "Trace to PO, delivery notes, and vendor statements.",
    },
    "PROC_MISSING_GSTIN": {
        "title": "Vendor invoices without GSTIN",
        "observation": "Material vendor invoices lack GSTIN details.",
        "impact": "Input tax credit eligibility and vendor validity concerns.",
        "recommendation": "Validate vendor master and GST registration.",
    },
    "PROC_CUTOFF": {
        "title": "Year-end procurement cut-off exceptions",
        "observation": "Vendor invoices dated in the financial year-end cut-off window.",
        "impact": "Elevated cut-off and expense recognition risk.",
        "recommendation": "Perform additional cut-off testing on goods receipt and invoice dates.",
    },
}


def _risk_level(count: int, default_score: int) -> str:
    weighted = count * default_score
    if weighted >= 40:
        return "high"
    if weighted >= 20:
        return "medium"
    return "low"


def generate_procurement_findings(db: Session, project_id: uuid.UUID) -> list[AuditFinding]:
    db.query(AuditFinding).filter(AuditFinding.project_id == project_id).delete()

    rules = {
        r.rule_code: r
        for r in db.query(RuleMaster).all()
        if r.rule_code.startswith("PROC_")
    }
    violations = (
        db.query(ProcurementRuleResult)
        .filter(
            ProcurementRuleResult.project_id == project_id,
            ProcurementRuleResult.triggered.is_(True),
        )
        .all()
    )

    grouped: dict[str, list[ProcurementRuleResult]] = defaultdict(list)
    for v in violations:
        grouped[v.rule_code].append(v)

    findings: list[AuditFinding] = []
    for code, items in grouped.items():
        template = PROCUREMENT_FINDING_TEMPLATES.get(code, {})
        rule = rules.get(code)
        default_score = rule.default_score if rule else 10

        findings.append(
            AuditFinding(
                project_id=project_id,
                rule_code=code,
                finding_title=template.get("title", f"{code} violations"),
                observation=template.get("observation", f"{len(items)} violations for {code}."),
                risk_level=_risk_level(len(items), default_score),
                impact=template.get("impact", "Potential procurement audit risk."),
                recommendation=template.get(
                    "recommendation", "Perform substantive AP procedures on flagged invoices."
                ),
                affected_count=len(items),
                source_record_ids=[str(v.procurement_invoice_id) for v in items],
                rule_content_version=rule.rule_content_version if rule else None,
            )
        )

    db.add_all(findings)
    db.commit()
    return findings
