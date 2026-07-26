from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, RevenueRuleResult, RuleMaster
from app.services.finding_evidence_linker import attach_auto_evidence_for_finding


REVENUE_FINDING_TEMPLATES: dict[str, dict] = {
    "REV_DUPLICATE_INVOICE": {
        "title": "Duplicate sales invoices identified",
        "observation": "Same invoice number and customer combination appears more than once.",
        "impact": "Risk of overstated revenue or duplicate billing.",
        "recommendation": "Verify source documents and confirm revenue recognition is not duplicated.",
    },
    "REV_CUTOFF": {
        "title": "Year-end revenue cut-off exceptions",
        "observation": "Invoices dated in the financial year-end cut-off window.",
        "impact": "Elevated cut-off and earnings management risk.",
        "recommendation": "Perform additional cut-off testing on delivery and billing dates.",
    },
    "REV_GST_MISMATCH": {
        "title": "GST computation mismatches on invoices",
        "observation": "GST amount inconsistent with taxable value at standard rates.",
        "impact": "Indirect tax and revenue accuracy may be misstated.",
        "recommendation": "Reconcile with GSTR-1 and validate tax rate applied per line item.",
    },
    "REV_ROUND_AMOUNT": {
        "title": "Round-figure invoice amounts detected",
        "observation": "Sales invoices with round total amounts were identified.",
        "impact": "May indicate estimates or manual billing adjustments.",
        "recommendation": "Trace to contracts, delivery challans, and e-invoices.",
    },
    "REV_HIGH_VALUE": {
        "title": "High-value sales invoices flagged",
        "observation": "Invoices exceed the engagement large-value threshold.",
        "impact": "Material revenue items require enhanced substantive procedures.",
        "recommendation": "Obtain contracts, delivery proof, and customer confirmations.",
    },
    "REV_MISSING_GSTIN": {
        "title": "B2B invoices without customer GSTIN",
        "observation": "Material invoices lack customer GSTIN details.",
        "impact": "Compliance and revenue authenticity concerns for B2B sales.",
        "recommendation": "Validate customer master and GST registration status.",
    },
    "REV_UNPAID_LARGE": {
        "title": "Large unpaid receivables identified",
        "observation": "High-value invoices remain unpaid or partially paid.",
        "impact": "Collectibility and revenue existence risk.",
        "recommendation": "Perform customer balance confirmation and subsequent receipts testing.",
    },
}


def _risk_level(count: int, default_score: int) -> str:
    weighted = count * default_score
    if weighted >= 40:
        return "high"
    if weighted >= 20:
        return "medium"
    return "low"


def generate_revenue_findings(db: Session, project_id: uuid.UUID) -> list[AuditFinding]:
    db.query(AuditFinding).filter(AuditFinding.project_id == project_id).delete()

    rules = {
        r.rule_code: r
        for r in db.query(RuleMaster).all()
        if r.rule_code.startswith("REV_")
    }
    violations = (
        db.query(RevenueRuleResult)
        .filter(RevenueRuleResult.project_id == project_id, RevenueRuleResult.triggered.is_(True))
        .all()
    )

    grouped: dict[str, list[RevenueRuleResult]] = defaultdict(list)
    for v in violations:
        grouped[v.rule_code].append(v)

    findings: list[AuditFinding] = []
    for code, items in grouped.items():
        template = REVENUE_FINDING_TEMPLATES.get(code, {})
        rule = rules.get(code)
        default_score = rule.default_score if rule else 10
        invoice_ids = [str(v.revenue_invoice_id) for v in items]

        findings.append(
            AuditFinding(
                project_id=project_id,
                rule_code=code,
                finding_title=template.get("title", f"{code} violations"),
                observation=template.get("observation", f"{len(items)} violations for {code}."),
                risk_level=_risk_level(len(items), default_score),
                impact=template.get("impact", "Potential revenue audit risk requiring follow-up."),
                recommendation=template.get(
                    "recommendation", "Perform substantive revenue procedures on flagged invoices."
                ),
                affected_count=len(items),
                source_record_ids=invoice_ids,
                rule_content_version=rule.rule_content_version if rule else None,
            )
        )

    db.add_all(findings)
    db.flush()
    for finding in findings:
        attach_auto_evidence_for_finding(db, finding)
    db.commit()
    return findings
