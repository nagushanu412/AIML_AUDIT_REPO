from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import RevenueInvoice, RevenueRiskScore, RevenueRuleResult, RuleMaster


def _category(total: int) -> str:
    if total >= 40:
        return "high"
    if total >= 20:
        return "medium"
    return "low"


def run_revenue_risk_scoring(db: Session, project_id: uuid.UUID) -> dict:
    rule_scores = {
        r.rule_code: r.default_score
        for r in db.query(RuleMaster).filter(RuleMaster.is_active.is_(True)).all()
        if r.rule_code.startswith("REV_")
    }

    violations = (
        db.query(RevenueRuleResult)
        .filter(RevenueRuleResult.project_id == project_id, RevenueRuleResult.triggered.is_(True))
        .all()
    )

    by_invoice: dict[uuid.UUID, dict] = defaultdict(lambda: {"total": 0, "breakdown": {}})

    for v in violations:
        score = rule_scores.get(v.rule_code, 10)
        data = by_invoice[v.revenue_invoice_id]
        data["total"] += score
        data["breakdown"][v.rule_code] = data["breakdown"].get(v.rule_code, 0) + score

    db.query(RevenueRiskScore).filter(RevenueRiskScore.project_id == project_id).delete()

    invoices = (
        db.query(RevenueInvoice)
        .filter(RevenueInvoice.project_id == project_id)
        .order_by(RevenueInvoice.invoice_date)
        .all()
    )

    counts = {"high": 0, "medium": 0, "low": 0}
    models: list[RevenueRiskScore] = []

    for inv in invoices:
        data = by_invoice.get(inv.id, {"total": 0, "breakdown": {}})
        category = _category(data["total"])
        counts[category] += 1
        models.append(
            RevenueRiskScore(
                project_id=project_id,
                revenue_invoice_id=inv.id,
                total_score=data["total"],
                risk_category=category,
                rule_breakdown=data["breakdown"],
            )
        )

    db.add_all(models)
    db.commit()

    total = len(invoices)
    return {
        "project_id": project_id,
        "total_invoices_scored": total,
        "high_risk": counts["high"],
        "medium_risk": counts["medium"],
        "low_risk": counts["low"],
        "message": f"Scored {total} invoices: {counts['high']} high, {counts['medium']} medium, {counts['low']} low risk.",
    }


def get_revenue_risk_scores(
    db: Session,
    project_id: uuid.UUID,
    *,
    risk_category: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    query = (
        db.query(RevenueRiskScore, RevenueInvoice)
        .join(RevenueInvoice, RevenueInvoice.id == RevenueRiskScore.revenue_invoice_id)
        .filter(RevenueRiskScore.project_id == project_id)
    )
    if risk_category:
        query = query.filter(RevenueRiskScore.risk_category == risk_category.lower())

    rows = (
        query.order_by(RevenueRiskScore.total_score.desc(), RevenueInvoice.invoice_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": rs.id,
            "revenue_invoice_id": rs.revenue_invoice_id,
            "total_score": rs.total_score,
            "risk_category": rs.risk_category,
            "rule_breakdown": rs.rule_breakdown,
            "invoice_no": inv.invoice_no,
            "invoice_date": inv.invoice_date,
            "customer_name": inv.customer_name,
            "total_amount": inv.total_amount,
            "gst_amount": inv.gst_amount,
            "payment_status": inv.payment_status,
        }
        for rs, inv in rows
    ]
