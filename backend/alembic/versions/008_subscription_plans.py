"""Subscription plans and organization subscriptions

Revision ID: 008
Revises: 007
Create Date: 2026-06-28

Milestone 2 — Subscription Plans.
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SUBSCRIPTION_STATUSES = ("trialing", "active", "past_due", "cancelled", "expired")

ALL_MODULE_CODES = [
    "JOURNAL_ENTRY_TESTING",
    "REVENUE_TESTING",
    "PROCUREMENT_TESTING",
    "LEDGER_SCRUTINY",
    "DUPLICATE_PAYMENT",
    "BANK_RECONCILIATION",
    "PO_MATCHING",
    "VENDOR_INVOICE",
    "EXPENSE_CLAIM",
    "FIXED_ASSET",
    "DEPRECIATION",
    "TDS_CHECKING",
    "GST_MISMATCH",
    "GST_ITC",
    "CUSTOMER_BALANCE",
    "PAYROLL",
    "USER_ACCESS",
    "SOD",
    "COMPLIANCE",
    "DOC_MATCHING",
    "EXCEPTION_REPORT",
    "INVOICE_CHECKING",
]

BUILT_MODULE_CODES = [
    "JOURNAL_ENTRY_TESTING",
    "REVENUE_TESTING",
    "PROCUREMENT_TESTING",
]

PLAN_SEED = [
    {
        "id": uuid.UUID("a1000001-0000-4000-8000-000000000001"),
        "code": "free",
        "name": "Free",
        "description": "Trial tier for solo auditors exploring AIML Audit.",
        "max_users": 2,
        "max_clients": 3,
        "max_engagements": 5,
        "max_storage_bytes": 104_857_600,
        "monthly_ai_credits": 10,
        "monthly_uploads": 10,
        "max_reports": 5,
        "enabled_module_codes": ["JOURNAL_ENTRY_TESTING"],
        "api_rate_limit": 60,
        "support_level": "email",
        "display_order": 1,
        "is_active": True,
    },
    {
        "id": uuid.UUID("a1000002-0000-4000-8000-000000000002"),
        "code": "starter",
        "name": "Starter",
        "description": "Small CA practice with core audit modules.",
        "max_users": 10,
        "max_clients": 25,
        "max_engagements": 50,
        "max_storage_bytes": 1_073_741_824,
        "monthly_ai_credits": 100,
        "monthly_uploads": 100,
        "max_reports": 50,
        "enabled_module_codes": BUILT_MODULE_CODES,
        "api_rate_limit": 120,
        "support_level": "email",
        "display_order": 2,
        "is_active": True,
    },
    {
        "id": uuid.UUID("a1000003-0000-4000-8000-000000000003"),
        "code": "professional",
        "name": "Professional",
        "description": "Mid-size audit firm with full module catalog access.",
        "max_users": 50,
        "max_clients": 200,
        "max_engagements": 500,
        "max_storage_bytes": 10_737_418_240,
        "monthly_ai_credits": 1000,
        "monthly_uploads": 1000,
        "max_reports": 500,
        "enabled_module_codes": ALL_MODULE_CODES,
        "api_rate_limit": 300,
        "support_level": "priority",
        "display_order": 3,
        "is_active": True,
    },
    {
        "id": uuid.UUID("a1000004-0000-4000-8000-000000000004"),
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Large firms and Big4-style practices with high limits.",
        "max_users": 9999,
        "max_clients": 99999,
        "max_engagements": 99999,
        "max_storage_bytes": 107_374_182_400,
        "monthly_ai_credits": 10000,
        "monthly_uploads": 10000,
        "max_reports": 99999,
        "enabled_module_codes": ALL_MODULE_CODES,
        "api_rate_limit": 1000,
        "support_level": "dedicated",
        "display_order": 4,
        "is_active": True,
    },
]


def upgrade() -> None:
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("max_clients", sa.Integer(), nullable=False),
        sa.Column("max_engagements", sa.Integer(), nullable=False),
        sa.Column("max_storage_bytes", sa.BigInteger(), nullable=False),
        sa.Column("monthly_ai_credits", sa.Integer(), nullable=False),
        sa.Column("monthly_uploads", sa.Integer(), nullable=False),
        sa.Column("max_reports", sa.Integer(), nullable=False),
        sa.Column(
            "enabled_module_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("api_rate_limit", sa.Integer(), nullable=False),
        sa.Column("support_level", sa.String(50), nullable=False, server_default="email"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
    )
    op.create_index("ix_subscription_plans_code", "subscription_plans", ["code"])

    op.create_table(
        "organization_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"status IN {SUBSCRIPTION_STATUSES}",
            name="ck_organization_subscriptions_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_plan_id"],
            ["subscription_plans.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organization_subscriptions_org_id",
        "organization_subscriptions",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_subscriptions_status",
        "organization_subscriptions",
        ["status"],
    )

    plans_table = sa.table(
        "subscription_plans",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("max_users", sa.Integer),
        sa.column("max_clients", sa.Integer),
        sa.column("max_engagements", sa.Integer),
        sa.column("max_storage_bytes", sa.BigInteger),
        sa.column("monthly_ai_credits", sa.Integer),
        sa.column("monthly_uploads", sa.Integer),
        sa.column("max_reports", sa.Integer),
        sa.column("enabled_module_codes", postgresql.JSONB),
        sa.column("api_rate_limit", sa.Integer),
        sa.column("support_level", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        plans_table,
        [
            {
                **row,
                "enabled_module_codes": row["enabled_module_codes"],
            }
            for row in PLAN_SEED
        ],
    )

    free_plan_id = PLAN_SEED[0]["id"]
    conn = op.get_bind()
    org_rows = conn.execute(sa.text("SELECT id FROM organizations")).fetchall()
    subs_table = sa.table(
        "organization_subscriptions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("organization_id", postgresql.UUID(as_uuid=True)),
        sa.column("subscription_plan_id", postgresql.UUID(as_uuid=True)),
        sa.column("status", sa.String),
    )
    if org_rows:
        op.bulk_insert(
            subs_table,
            [
                {
                    "id": uuid.uuid4(),
                    "organization_id": row[0],
                    "subscription_plan_id": free_plan_id,
                    "status": "active",
                }
                for row in org_rows
            ],
        )


def downgrade() -> None:
    op.drop_index("ix_organization_subscriptions_status", table_name="organization_subscriptions")
    op.drop_index("ix_organization_subscriptions_org_id", table_name="organization_subscriptions")
    op.drop_table("organization_subscriptions")
    op.drop_index("ix_subscription_plans_code", table_name="subscription_plans")
    op.drop_table("subscription_plans")
