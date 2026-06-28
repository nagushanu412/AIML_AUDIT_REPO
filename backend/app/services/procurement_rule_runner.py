from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditProject, ProcurementInvoice, ProcurementRuleResult, RuleMaster
from app.services.procurement_constants import PROCUREMENT_RULE_PREFIX
from app.services.procurement_rule_engine import evaluate_procurement_rules


def _invoice_to_dict(inv: ProcurementInvoice) -> dict:
    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "invoice_date": inv.invoice_date,
        "vendor_name": inv.vendor_name,
        "vendor_gstin": inv.vendor_gstin,
        "po_number": inv.po_number,
        "taxable_amount": inv.taxable_amount,
        "gst_amount": inv.gst_amount,
        "total_amount": inv.total_amount,
        "payment_status": inv.payment_status,
        "reference_no": inv.reference_no,
    }


def _load_procurement_project(db: Session, project_id: uuid.UUID) -> AuditProject:
    project = (
        db.query(AuditProject)
        .options(joinedload(AuditProject.engagement))
        .filter(AuditProject.id == project_id)
        .first()
    )
    if not project:
        raise ValueError(f"Audit project not found: {project_id}")
    if project.project_type != "procurement_testing":
        raise ValueError("Project is not a procurement testing project.")
    return project


def run_procurement_rules_for_project(db: Session, project_id: uuid.UUID) -> dict:
    project = _load_procurement_project(db, project_id)
    engagement = project.engagement

    invoices = (
        db.query(ProcurementInvoice)
        .filter(ProcurementInvoice.project_id == project.id)
        .order_by(ProcurementInvoice.invoice_date)
        .all()
    )

    rules_master = {
        r.rule_code: r
        for r in db.query(RuleMaster)
        .filter(
            RuleMaster.is_active.is_(True),
            RuleMaster.rule_code.like(f"{PROCUREMENT_RULE_PREFIX}%"),
        )
        .all()
    }

    if not invoices:
        return {
            "project_id": project.id,
            "total_invoices_analyzed": 0,
            "total_violations_found": 0,
            "violations_by_rule": {},
            "rule_summary": [
                {
                    "rule_code": r.rule_code,
                    "rule_name": r.rule_name,
                    "description": r.description or "",
                    "violation_count": 0,
                }
                for r in rules_master.values()
            ],
            "message": "No vendor invoices found. Upload procurement register before running rules.",
        }

    rule_configs = {code: dict(r.config_schema or {}) for code, r in rules_master.items()}
    if "PROC_HIGH_VALUE" in rule_configs:
        rule_configs["PROC_HIGH_VALUE"]["threshold"] = float(engagement.large_value_threshold)
    if "PROC_MISSING_PO" in rule_configs:
        rule_configs["PROC_MISSING_PO"]["min_amount"] = float(engagement.large_value_threshold)

    violations = evaluate_procurement_rules(
        [_invoice_to_dict(i) for i in invoices],
        high_value_threshold=engagement.large_value_threshold,
        financial_year_end=engagement.financial_year_end,
        rule_configs=rule_configs,
        active_rule_codes=set(rules_master.keys()),
    )

    db.query(ProcurementRuleResult).filter(ProcurementRuleResult.project_id == project.id).delete()

    db.add_all(
        [
            ProcurementRuleResult(
                project_id=project.id,
                procurement_invoice_id=v["procurement_invoice_id"],
                rule_id=rules_master[v["rule_code"]].id if v["rule_code"] in rules_master else None,
                rule_code=v["rule_code"],
                rule_name=v["rule_name"],
                triggered=True,
                details=v["details"],
            )
            for v in violations
        ]
    )
    db.commit()

    violations_by_rule = dict(Counter(v["rule_code"] for v in violations))
    return {
        "project_id": project.id,
        "total_invoices_analyzed": len(invoices),
        "total_violations_found": len(violations),
        "violations_by_rule": violations_by_rule,
        "rule_summary": [
            {
                "rule_code": r.rule_code,
                "rule_name": r.rule_name,
                "description": r.description or "",
                "violation_count": violations_by_rule.get(r.rule_code, 0),
            }
            for r in sorted(rules_master.values(), key=lambda x: x.rule_code)
        ],
        "message": f"Analyzed {len(invoices)} invoices. Found {len(violations)} rule violations.",
    }
