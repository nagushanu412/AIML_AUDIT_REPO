from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, RuleMaster, RuleResult


FINDING_TEMPLATES: dict[str, dict] = {
    "LARGE_VALUE": {
        "title": "Large value journal entries identified",
        "observation": "One or more journal entries exceed the engagement large-value threshold.",
        "impact": "Material misstatement risk if unsupported or improperly authorized.",
        "recommendation": "Obtain supporting documentation and verify management authorization.",
    },
    "YEAR_END": {
        "title": "Year-end journal entries flagged",
        "observation": "Entries posted in the last 7 days of the financial year.",
        "impact": "Elevated risk of earnings management or cut-off errors.",
        "recommendation": "Perform additional cut-off testing and review post-closing entries.",
    },
    "ROUND_AMOUNT": {
        "title": "Round-amount postings detected",
        "observation": "Journal entries with round figure amounts were identified.",
        "impact": "May indicate estimates or manual adjustments requiring scrutiny.",
        "recommendation": "Trace to source documents and assess business rationale.",
    },
    "WEEKEND": {
        "title": "Weekend postings identified",
        "observation": "Journal entries posted on Saturday or Sunday.",
        "impact": "Unusual timing may indicate override of controls.",
        "recommendation": "Review user access logs and approval workflow for weekend activity.",
    },
    "SUSPENSE_ACCOUNT": {
        "title": "Suspense or clearing account usage",
        "observation": "Entries posted to suspense, clearing, or adjustment accounts.",
        "impact": "Incomplete classification may mask errors or fraud.",
        "recommendation": "Confirm timely clearance and proper final account classification.",
    },
    "MANUAL_JOURNAL": {
        "title": "Manual journal adjustments flagged",
        "observation": "Descriptions indicate manual adjustments or corrections.",
        "impact": "Manual entries are higher inherent risk for misstatement.",
        "recommendation": "Inspect supporting schedules and reviewer sign-off.",
    },
    "UNUSUAL_POSTING": {
        "title": "Unusual posting volume by user",
        "observation": "Certain users posted significantly more entries than peers.",
        "impact": "Concentration of activity may indicate control override.",
        "recommendation": "Interview responsible users and test sample of their entries.",
    },
}


def _risk_level(count: int, default_score: int) -> str:
    weighted = count * default_score
    if weighted >= 40:
        return "high"
    if weighted >= 20:
        return "medium"
    return "low"


def generate_findings(db: Session, project_id: uuid.UUID) -> list[AuditFinding]:
    db.query(AuditFinding).filter(AuditFinding.project_id == project_id).delete()

    rules = {r.rule_code: r for r in db.query(RuleMaster).all()}
    violations = (
        db.query(RuleResult)
        .filter(RuleResult.project_id == project_id, RuleResult.triggered.is_(True))
        .all()
    )

    grouped: dict[str, list[RuleResult]] = defaultdict(list)
    for v in violations:
        grouped[v.rule_code].append(v)

    findings: list[AuditFinding] = []
    for code, items in grouped.items():
        template = FINDING_TEMPLATES.get(code, {})
        rule = rules.get(code)
        default_score = rule.default_score if rule else 10
        entry_ids = [str(v.journal_entry_id) for v in items]

        findings.append(
            AuditFinding(
                project_id=project_id,
                rule_code=code,
                finding_title=template.get("title", f"{code} violations"),
                observation=template.get("observation", f"{len(items)} violations for {code}."),
                risk_level=_risk_level(len(items), default_score),
                impact=template.get("impact", "Potential audit risk requiring follow-up."),
                recommendation=template.get(
                    "recommendation", "Perform substantive procedures on flagged entries."
                ),
                affected_count=len(items),
                journal_entry_ids=entry_ids,
            )
        )

    db.add_all(findings)
    db.commit()
    return findings
