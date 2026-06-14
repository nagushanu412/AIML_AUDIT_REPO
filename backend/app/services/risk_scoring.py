from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import JournalEntry, RiskScore, RuleMaster, RuleResult


def _category(total: int) -> str:
    if total >= 40:
        return "high"
    if total >= 20:
        return "medium"
    return "low"


def run_risk_scoring(db: Session, project_id: uuid.UUID) -> dict:
    rule_scores = {
        r.rule_code: r.default_score
        for r in db.query(RuleMaster).filter(RuleMaster.is_active.is_(True)).all()
    }

    violations = (
        db.query(RuleResult)
        .filter(RuleResult.project_id == project_id, RuleResult.triggered.is_(True))
        .all()
    )

    by_entry: dict[uuid.UUID, dict] = defaultdict(lambda: {"total": 0, "breakdown": {}})

    for v in violations:
        score = rule_scores.get(v.rule_code, 10)
        entry_data = by_entry[v.journal_entry_id]
        entry_data["total"] += score
        entry_data["breakdown"][v.rule_code] = (
            entry_data["breakdown"].get(v.rule_code, 0) + score
        )

    db.query(RiskScore).filter(RiskScore.project_id == project_id).delete()

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.project_id == project_id)
        .order_by(JournalEntry.posting_date)
        .all()
    )

    counts = {"high": 0, "medium": 0, "low": 0}
    models: list[RiskScore] = []

    for entry in entries:
        data = by_entry.get(entry.id, {"total": 0, "breakdown": {}})
        category = _category(data["total"])
        counts[category] += 1
        models.append(
            RiskScore(
                project_id=project_id,
                journal_entry_id=entry.id,
                total_score=data["total"],
                risk_category=category,
                rule_breakdown=data["breakdown"],
            )
        )

    db.add_all(models)
    db.commit()

    total = len(entries)

    return {
        "project_id": project_id,
        "total_entries_scored": total,
        "high_risk": counts["high"],
        "medium_risk": counts["medium"],
        "low_risk": counts["low"],
        "message": f"Scored {total} entries: {counts['high']} high, {counts['medium']} medium, {counts['low']} low risk.",
    }


def get_risk_scores(
    db: Session,
    project_id: uuid.UUID,
    *,
    risk_category: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    query = (
        db.query(RiskScore, JournalEntry)
        .join(JournalEntry, JournalEntry.id == RiskScore.journal_entry_id)
        .filter(RiskScore.project_id == project_id)
    )
    if risk_category:
        query = query.filter(RiskScore.risk_category == risk_category.lower())

    rows = (
        query.order_by(RiskScore.total_score.desc(), JournalEntry.posting_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": rs.id,
            "journal_entry_id": rs.journal_entry_id,
            "total_score": rs.total_score,
            "risk_category": rs.risk_category,
            "rule_breakdown": rs.rule_breakdown,
            "journal_id": entry.journal_id,
            "posting_date": entry.posting_date,
            "account_name": entry.account_name,
            "amount": entry.amount,
            "user_id": entry.user_id,
        }
        for rs, entry in rows
    ]
