"""Procurement testing tables and rules

Revision ID: 006
Revises: 005
Create Date: 2026-06-27

"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROCUREMENT_RULES = [
    (
        "PROC_DUPLICATE_PAYMENT",
        "Duplicate Vendor Payment",
        "Same vendor and invoice number appears more than once.",
        15,
        {"match_fields": ["invoice_no", "vendor_name"]},
    ),
    (
        "PROC_MISSING_PO",
        "Missing Purchase Order",
        "High-value vendor invoice without PO reference.",
        12,
        {"min_amount": 100000},
    ),
    (
        "PROC_GST_MISMATCH",
        "GST Input Mismatch",
        "GST amount inconsistent with standard rates on taxable value.",
        15,
        {"allowed_rates": [0, 5, 12, 18, 28], "tolerance_pct": 1.0},
    ),
    (
        "PROC_HIGH_VALUE",
        "High-Value Vendor Invoice",
        "Invoice total exceeds the engagement threshold.",
        12,
        {"threshold": 100000},
    ),
    (
        "PROC_ROUND_AMOUNT",
        "Round Invoice Amount",
        "Vendor invoice total is a round figure.",
        8,
        {"suffixes": [1000, 5000, 10000, 50000, 100000]},
    ),
    (
        "PROC_MISSING_GSTIN",
        "Missing Vendor GSTIN",
        "Material vendor invoice without GSTIN.",
        10,
        {"min_amount": 250000},
    ),
    (
        "PROC_CUTOFF",
        "Year-End Cut-Off",
        "Vendor invoice dated within year-end cut-off window.",
        12,
        {"days_before": 7},
    ),
]


def upgrade() -> None:
    op.create_table(
        "procurement_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("vendor_gstin", sa.String(50)),
        sa.Column("po_number", sa.String(100)),
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
    op.create_index("ix_procurement_invoices_project_id", "procurement_invoices", ["project_id"])

    op.create_table(
        "procurement_rule_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procurement_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["procurement_invoice_id"], ["procurement_invoices.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["rule_id"], ["rules_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "procurement_risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procurement_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            name="ck_procurement_risk_category",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["audit_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["procurement_invoice_id"], ["procurement_invoices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "procurement_invoice_id", name="uq_procurement_risk_project_invoice"
        ),
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
            for code, name, desc, score, config in PROCUREMENT_RULES
        ],
    )


def downgrade() -> None:
    for code, _, _, _, _ in PROCUREMENT_RULES:
        op.execute(sa.text(f"DELETE FROM rules_master WHERE rule_code = '{code}'"))
    op.drop_table("procurement_risk_scores")
    op.drop_table("procurement_rule_results")
    op.drop_table("procurement_invoices")
