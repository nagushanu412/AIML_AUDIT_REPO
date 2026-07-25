"""Remediation Milestone 1 Step 2 — denormalized organization_id coverage."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, validate_database_connection
from app.models.audit import JournalEntry
from app.models.organization_id_events import register_organization_id_listeners

register_organization_id_listeners()

STEP2_TABLES = (
    "journal_entries",
    "revenue_invoices",
    "procurement_invoices",
    "audit_findings",
    "rule_results",
    "revenue_rule_results",
    "procurement_rule_results",
    "risk_scores",
    "revenue_risk_scores",
    "procurement_risk_scores",
    "reports",
    "evidence_links",
    "engagement_enabled_modules",
    "engagement_team_members",
    "review_comments",
    "approvals",
    "evidence",
    "workpapers",
    "audit_logs",
    "feature_flags",
    "finding_relationships",
    "module_analysis_runs",
)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


@requires_db
def test_step2_tables_organization_id_not_null_and_zero_nulls():
    db = SessionLocal()
    try:
        for table in STEP2_TABLES:
            nullable = db.execute(
                text(
                    """
                    SELECT is_nullable
                    FROM information_schema.columns
                    WHERE table_name = :table
                      AND column_name = 'organization_id'
                    """
                ),
                {"table": table},
            ).scalar()
            assert nullable == "NO", f"{table}.organization_id is_nullable={nullable}"

            nulls = db.execute(
                text(f"SELECT count(*) FROM {table} WHERE organization_id IS NULL")
            ).scalar()
            assert int(nulls or 0) == 0, f"{table} still has NULL organization_id rows"
    finally:
        db.close()


@requires_db
def test_journal_entry_organization_id_null_rejected_at_database():
    db = SessionLocal()
    try:
        project_id = db.execute(text("SELECT id FROM audit_projects LIMIT 1")).scalar()
        if project_id is None:
            pytest.skip("No audit_projects available")

        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    """
                    INSERT INTO journal_entries (
                        id, project_id, organization_id, journal_id, posting_date,
                        account_code, account_name, amount, debit_credit, user_id
                    )
                    VALUES (
                        :id, :project_id, NULL, 'NULL-ORG-TEST', :posting_date,
                        '1000', 'Cash', 100, 'Debit', 'tester'
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "project_id": str(project_id),
                    "posting_date": date(2026, 4, 1),
                },
            )
            db.commit()
        db.rollback()
    finally:
        db.close()


@requires_db
def test_before_insert_sets_organization_id_from_project():
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                """
                SELECT p.id AS project_id, e.organization_id
                FROM audit_projects p
                JOIN audit_engagements e ON e.id = p.engagement_id
                LIMIT 1
                """
            )
        ).mappings().first()
        if row is None:
            pytest.skip("No project/engagement available")

        entry = JournalEntry(
            project_id=row["project_id"],
            journal_id=f"AUTO-ORG-{uuid.uuid4().hex[:8]}",
            posting_date=date(2026, 4, 1),
            account_code="1000",
            account_name="Cash",
            amount=10,
            debit_credit="Debit",
            user_id="auto-org-test",
        )
        assert entry.organization_id is None or entry.organization_id == row["organization_id"]
        db.add(entry)
        db.flush()
        assert entry.organization_id == row["organization_id"]
        db.rollback()
    finally:
        db.close()
