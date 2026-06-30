from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.models.audit import (
    AuditEngagement,
    AuditProject,
    Client,
    JournalEntry,
    RiskScore,
    RuleResult,
)
from app.services.project_access import client_list_filter
from app.services.tenant_context import TenantContext

LEGACY_CLIENT_NAMES = ("Default Client", "Migrated Client")


def get_dashboard_summary(db: Session, tenant: TenantContext) -> dict:
    client_ids = [
        c.id
        for c in db.query(Client)
        .filter(
            client_list_filter(tenant),
            Client.name.notin_(LEGACY_CLIENT_NAMES),
        )
        .all()
    ]

    if not client_ids:
        return {
            "total_clients": 0,
            "total_engagements": 0,
            "total_projects": 0,
            "total_journal_entries": 0,
            "total_violations": 0,
            "high_risk_entries": 0,
            "medium_risk_entries": 0,
            "low_risk_entries": 0,
            "risk_distribution": {"high": 0, "medium": 0, "low": 0},
            "violations_by_rule": {},
            "recent_activities": [],
        }

    engagement_ids = [
        e.id
        for e in db.query(AuditEngagement.id)
        .filter(AuditEngagement.client_id.in_(client_ids))
        .all()
    ]

    project_ids = [
        p.id
        for p in db.query(AuditProject.id)
        .filter(AuditProject.engagement_id.in_(engagement_ids))
        .all()
    ]

    total_entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.project_id.in_(project_ids))
        .count()
        if project_ids
        else 0
    )
    total_violations = (
        db.query(RuleResult)
        .filter(RuleResult.project_id.in_(project_ids), RuleResult.triggered.is_(True))
        .count()
        if project_ids
        else 0
    )
    risk_distribution = {"high": 0, "medium": 0, "low": 0}
    if project_ids:
        for cat in risk_distribution:
            risk_distribution[cat] = (
                db.query(RiskScore)
                .filter(
                    RiskScore.project_id.in_(project_ids),
                    RiskScore.risk_category == cat,
                )
                .count()
            )

    violations_by_rule: dict[str, int] = {}
    if project_ids:
        rule_rows = (
            db.query(RuleResult.rule_code)
            .filter(
                RuleResult.project_id.in_(project_ids),
                RuleResult.triggered.is_(True),
            )
            .all()
        )
        violations_by_rule = dict(Counter(code for (code,) in rule_rows))

    recent_projects = (
        db.query(AuditProject)
        .filter(AuditProject.engagement_id.in_(engagement_ids))
        .order_by(AuditProject.updated_at.desc())
        .limit(5)
        .all()
        if engagement_ids
        else []
    )

    activities = [
        {
            "type": "project",
            "title": p.name,
            "detail": f"{p.total_entries} entries · {p.status}",
            "timestamp": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in recent_projects
    ]

    return {
        "total_clients": len(client_ids),
        "total_engagements": len(engagement_ids),
        "total_projects": len(project_ids),
        "total_journal_entries": total_entries,
        "total_violations": total_violations,
        "high_risk_entries": risk_distribution["high"],
        "medium_risk_entries": risk_distribution["medium"],
        "low_risk_entries": risk_distribution["low"],
        "risk_distribution": risk_distribution,
        "violations_by_rule": violations_by_rule,
        "recent_activities": activities,
    }
