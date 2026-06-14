from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.audit import AuditEngagement, AuditProject, Client, RuleMaster, User
from app.services.auth_service import ensure_demo_user
from app.services.rule_config import DEFAULT_RULE_CONFIGS


def ensure_rule_configs(db: Session) -> None:
    """Backfill empty config_schema rows (safe if migration 004 already ran)."""
    updated = False
    for rule in db.query(RuleMaster).all():
        if not rule.config_schema:
            rule.config_schema = DEFAULT_RULE_CONFIGS.get(rule.rule_code, {})
            updated = True
    if updated:
        db.commit()


def seed_demo_hierarchy(db: Session) -> None:
    ensure_rule_configs(db)
    user = ensure_demo_user(db)
    client = (
        db.query(Client)
        .filter(Client.user_id == user.id, Client.name == "ABC Manufacturing")
        .first()
    )
    if not client:
        client = Client(
            user_id=user.id,
            name="ABC Manufacturing",
            industry="Manufacturing",
            contact_person="Nagarajan",
            status="active",
        )
        db.add(client)
        db.flush()

    engagements_data = [
        ("FY 2024-25", date(2025, 3, 31)),
        ("FY 2025-26", date(2026, 3, 31)),
        ("FY 2026-27", date(2027, 3, 31)),
    ]
    for fy, fy_end in engagements_data:
        existing = (
            db.query(AuditEngagement)
            .filter(
                AuditEngagement.client_id == client.id,
                AuditEngagement.financial_year == fy,
            )
            .first()
        )
        if existing:
            engagement = existing
        else:
            engagement = AuditEngagement(
                client_id=client.id,
                financial_year=fy,
                audit_type="Statutory",
                status="active",
                start_date=date(fy_end.year - 1, 4, 1),
                end_date=fy_end,
                financial_year_end=fy_end,
                large_value_threshold=Decimal("100000"),
            )
            db.add(engagement)
            db.flush()

        for pname, ptype in [
            ("Journal Testing", "journal_testing"),
            ("Revenue Testing", "revenue_testing"),
            ("Procurement Testing", "procurement_testing"),
        ]:
            exists = (
                db.query(AuditProject)
                .filter(
                    AuditProject.engagement_id == engagement.id,
                    AuditProject.name == pname,
                )
                .first()
            )
            if not exists:
                db.add(
                    AuditProject(
                        engagement_id=engagement.id,
                        name=pname,
                        project_type=ptype,
                        status="active",
                    )
                )
    db.commit()
