"""Revenue testing tables and rules

Revision ID: 005
Revises: 004
Create Date: 2026-06-19

"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REVENUE_RULES = [
    (
        "REV_DUPLICATE_INVOICE",
        "Duplicate Invoice",
        "Same invoice number and customer appears more than once.",
        15,
        {"match_fields": ["invoice_no", "customer_name"]},
    ),
    (
        "REV_CUTOFF",
        "Year-End Cut-Off",
        "Invoice dated within the year-end cut-off window.",
        12,
        {"days_before": 7},
    ),
    (
        "REV_GST_MISMATCH",
        "GST Mismatch",
        "GST amount inconsistent with standard rates on taxable value.",
        15,
        {"allowed_rates": [0, 5, 12, 18, 28], "tolerance_pct": 1.0},
    ),
    (
        "REV_ROUND_AMOUNT",
        "Round Invoice Amount",
        "Invoice total is a round figure.",
        8,
        {"suffixes": [1000, 5000, 10000, 50000, 100000]},
    ),
    (
        "REV_HIGH_VALUE",
        "High-Value Invoice",
        "Invoice total exceeds the engagement threshold.",
        12,
        {"threshold": 100000},
    ),
    (
        "REV_MISSING_GSTIN",
        "Missing Customer GSTIN",
        "B2B-scale invoice without customer GSTIN.",
        10,
        {"min_amount": 250000},
    ),
    (
        "REV_UNPAID_LARGE",
        "Large Unpaid Invoice",
        "High-value invoice marked unpaid or partial.",
        10,
        {"min_amount": 500000, "statuses": ["unpaid", "partial"]},
    ),
]


def upgrade() -> None:
    op.create_table(
        "revenue_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_gstin", sa.String(50)),
        sa.Column("taxable_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("gst_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("payment_status", sa.String(50)),
        sa.Column("reference_no", sa.String(100)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["audit_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_revenue_invoices_project_id", "revenue_invoices", ["project_id"])

    op.create_table(
        "revenue_rule_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revenue_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True)),
        sa.Column("rule_code", sa.String(50), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("triggered", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("details", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["audit_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revenue_invoice_id"], ["revenue_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["rules_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_revenue_rule_results_project_id", "revenue_rule_results", ["project_id"])

    op.create_table(
        "revenue_risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revenue_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("risk_category", sa.String(20), nullable=False),
        sa.Column(
            "rule_breakdown",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "risk_category IN ('low', 'medium', 'high')",
            name="ck_revenue_risk_category",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["audit_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revenue_invoice_id"], ["revenue_invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "revenue_invoice_id", name="uq_revenue_risk_project_invoice"),
    )

    rules_table = sa.table(
        "rules_master",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_code", sa.String),
        sa.column("rule_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_score", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("config_schema", postgresql.JSONB),
    )
    op.bulk_insert(
        rules_table,
        [
            {
                "id": uuid.uuid4(),
                "rule_code": code,
                "rule_name": name,
                "description": desc,
                "default_score": score,
                "is_active": True,
                "config_schema": config,
            }
            for code, name, desc, score, config in REVENUE_RULES
        ],
    )


def downgrade() -> None:
    for code, _, _, _, _ in REVENUE_RULES:
        op.execute(sa.text(f"DELETE FROM rules_master WHERE rule_code = '{code}'"))
    op.drop_table("revenue_risk_scores")
    op.drop_table("revenue_rule_results")
    op.drop_table("revenue_invoices")
