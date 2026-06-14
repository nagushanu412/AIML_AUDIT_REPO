from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditProject, JournalEntry, RuleMaster, RuleResult
from app.services.rule_config import build_evaluation_context
from app.services.rule_engine import evaluate_rules


def _entry_to_dict(entry: JournalEntry) -> dict:
    return {
        "id": entry.id,
        "journal_id": entry.journal_id,
        "posting_date": entry.posting_date,
        "account_name": entry.account_name,
        "amount": entry.amount,
        "user_id": entry.user_id,
        "description": entry.description,
    }


def _load_project(db: Session, project_id: uuid.UUID) -> AuditProject:
    project = (
        db.query(AuditProject)
        .options(joinedload(AuditProject.engagement))
        .filter(AuditProject.id == project_id)
        .first()
    )
    if not project:
        raise ValueError(f"Audit project not found: {project_id}")
    return project


def run_rules_for_project(db: Session, project_id: uuid.UUID) -> dict:
    project = _load_project(db, project_id)
    engagement = project.engagement

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.project_id == project.id)
        .order_by(JournalEntry.posting_date)
        .all()
    )

    rules_master = {
        r.rule_code: r
        for r in db.query(RuleMaster).filter(RuleMaster.is_active.is_(True)).all()
    }

    if not entries:
        return {
            "project_id": project.id,
            "total_entries_analyzed": 0,
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
            "message": "No journal entries found. Upload data before running rules.",
        }

    entry_dicts = [_entry_to_dict(e) for e in entries]
    rule_configs, active_codes = build_evaluation_context(
        rules_master,
        engagement.large_value_threshold,
    )
    violations = evaluate_rules(
        entry_dicts,
        large_value_threshold=engagement.large_value_threshold,
        financial_year_end=engagement.financial_year_end,
        rule_configs=rule_configs,
        active_rule_codes=active_codes,
    )

    db.query(RuleResult).filter(RuleResult.project_id == project.id).delete()

    rule_models = [
        RuleResult(
            project_id=project.id,
            journal_entry_id=v["journal_entry_id"],
            rule_id=rules_master[v["rule_code"]].id if v["rule_code"] in rules_master else None,
            rule_code=v["rule_code"],
            rule_name=v["rule_name"],
            triggered=True,
            details=v["details"],
        )
        for v in violations
    ]
    db.add_all(rule_models)
    db.commit()

    violations_by_rule = dict(Counter(v["rule_code"] for v in violations))
    rule_summary = [
        {
            "rule_code": r.rule_code,
            "rule_name": r.rule_name,
            "description": r.description or "",
            "violation_count": violations_by_rule.get(r.rule_code, 0),
        }
        for r in sorted(rules_master.values(), key=lambda x: x.rule_code)
    ]

    return {
        "project_id": project.id,
        "total_entries_analyzed": len(entries),
        "total_violations_found": len(violations),
        "violations_by_rule": violations_by_rule,
        "rule_summary": rule_summary,
        "message": f"Analyzed {len(entries)} entries. Found {len(violations)} rule violations.",
    }


def get_rule_results(
    db: Session,
    project_id: uuid.UUID,
    *,
    rule_code: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    _load_project(db, project_id)

    query = (
        db.query(RuleResult, JournalEntry)
        .join(JournalEntry, JournalEntry.id == RuleResult.journal_entry_id)
        .filter(
            RuleResult.project_id == project_id,
            RuleResult.triggered.is_(True),
        )
    )

    if rule_code:
        query = query.filter(RuleResult.rule_code == rule_code.upper())

    rows = (
        query.order_by(JournalEntry.posting_date.desc(), RuleResult.rule_code)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": rr.id,
            "journal_entry_id": rr.journal_entry_id,
            "rule_code": rr.rule_code,
            "rule_name": rr.rule_name,
            "triggered": rr.triggered,
            "details": rr.details,
            "journal_id": entry.journal_id,
            "posting_date": entry.posting_date,
            "account_name": entry.account_name,
            "amount": entry.amount,
            "user_id": entry.user_id,
            "created_at": rr.created_at,
        }
        for rr, entry in rows
    ]
