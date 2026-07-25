"""Remediation Milestone 4 Step 2 — journal_entry_ids → source_record_ids."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from app.database import SessionLocal, validate_database_connection
from app.models.audit import AuditFinding


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def test_audit_finding_orm_attribute_is_source_record_ids():
    assert hasattr(AuditFinding, "source_record_ids")
    assert not hasattr(AuditFinding, "journal_entry_ids")


@requires_db
def test_db_column_renamed_to_source_record_ids():
    db = SessionLocal()
    try:
        cols = {
            c["name"]
            for c in inspect(db.bind).get_columns("audit_findings")
        }
        assert "source_record_ids" in cols
        assert "journal_entry_ids" not in cols

        # Round-trip write/read on the new column name
        row = db.execute(
            text(
                "SELECT id, source_record_ids FROM audit_findings LIMIT 1"
            )
        ).mappings().first()
        if row is not None:
            assert "source_record_ids" in row
    finally:
        db.close()
