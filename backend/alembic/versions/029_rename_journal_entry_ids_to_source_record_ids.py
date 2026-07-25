"""Remediation M4 Step 2 — rename audit_findings.journal_entry_ids

Revision ID: 029
Revises: 028
Create Date: 2026-07-25

Rename journal_entry_ids → source_record_ids. The column already holds
invoice IDs for Revenue/Procurement findings; the old name was module-specific.
Historical migrations (including 026) are left unchanged (ADR-006).
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "audit_findings",
        "journal_entry_ids",
        new_column_name="source_record_ids",
    )


def downgrade() -> None:
    op.alter_column(
        "audit_findings",
        "source_record_ids",
        new_column_name="journal_entry_ids",
    )
