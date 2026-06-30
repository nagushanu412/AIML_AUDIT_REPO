"""Finding lifecycle and status history

Revision ID: 016
Revises: 015
Create Date: 2026-06-07

Phase 2 Milestone 3 — Finding Lifecycle.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_findings",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
    )
    op.add_column(
        "audit_findings",
        sa.Column("management_response", sa.Text(), nullable=True),
    )
    op.add_column(
        "audit_findings",
        sa.Column(
            "remediation_status",
            sa.String(length=50),
            nullable=False,
            server_default="not_started",
        ),
    )
    op.add_column(
        "audit_findings",
        sa.Column("remediation_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "audit_findings",
        sa.Column("remediation_due_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "audit_findings",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "audit_findings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_audit_findings_updated_by",
        "audit_findings",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_audit_findings_status",
        "audit_findings",
        "status IN ('open', 'under_review', 'cleared', 'accepted', 'closed')",
    )
    op.create_check_constraint(
        "ck_audit_findings_remediation_status",
        "audit_findings",
        "remediation_status IN ('not_started', 'in_progress', 'completed', 'overdue')",
    )
    op.create_index("ix_audit_findings_status", "audit_findings", ["status"])

    op.create_table(
        "finding_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("management_response_snapshot", sa.Text(), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ("
            "'status_change', 'management_response', 'remediation_update', 'reopened'"
            ")",
            name="ck_finding_status_history_action",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"], ["audit_findings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_finding_status_history_finding_id",
        "finding_status_history",
        ["finding_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_finding_status_history_finding_id", table_name="finding_status_history")
    op.drop_table("finding_status_history")
    op.drop_index("ix_audit_findings_status", table_name="audit_findings")
    op.drop_constraint("ck_audit_findings_remediation_status", "audit_findings", type_="check")
    op.drop_constraint("ck_audit_findings_status", "audit_findings", type_="check")
    op.drop_constraint("fk_audit_findings_updated_by", "audit_findings", type_="foreignkey")
    op.drop_column("audit_findings", "updated_at")
    op.drop_column("audit_findings", "updated_by")
    op.drop_column("audit_findings", "remediation_due_date")
    op.drop_column("audit_findings", "remediation_notes")
    op.drop_column("audit_findings", "remediation_status")
    op.drop_column("audit_findings", "management_response")
    op.drop_column("audit_findings", "status")
