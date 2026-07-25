"""Remediation M3 Step 1 — audit_findings.reviewed_by / reviewed_at

Revision ID: 027
Revises: 026
Create Date: 2026-07-25
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_findings",
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "audit_findings",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_audit_findings_reviewed_by",
        "audit_findings",
        "users",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_audit_findings_reviewed_by", "audit_findings", ["reviewed_by"])


def downgrade() -> None:
    op.drop_index("ix_audit_findings_reviewed_by", table_name="audit_findings")
    op.drop_constraint("fk_audit_findings_reviewed_by", "audit_findings", type_="foreignkey")
    op.drop_column("audit_findings", "reviewed_at")
    op.drop_column("audit_findings", "reviewed_by")
