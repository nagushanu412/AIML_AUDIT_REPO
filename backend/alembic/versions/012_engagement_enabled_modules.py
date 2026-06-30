"""Engagement enabled modules

Revision ID: 012
Revises: 011
Create Date: 2026-06-07

Milestone 6 — Engagement Enabled Modules.
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROJECT_TYPE_MAP = {
    "journal_testing": "JOURNAL_ENTRY_TESTING",
    "revenue_testing": "REVENUE_TESTING",
    "procurement_testing": "PROCUREMENT_TESTING",
}


def upgrade() -> None:
    op.create_table(
        "engagement_enabled_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_catalog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enabled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("enabled_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["module_catalog_id"], ["audit_module_catalog.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["enabled_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "engagement_id",
            "module_catalog_id",
            name="uq_engagement_enabled_modules",
        ),
    )
    op.create_index(
        "ix_engagement_enabled_modules_engagement_id",
        "engagement_enabled_modules",
        ["engagement_id"],
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT DISTINCT ap.engagement_id, ap.project_type, amc.id AS module_catalog_id
            FROM audit_projects ap
            JOIN audit_module_catalog amc ON amc.code = CASE ap.project_type
                WHEN 'journal_testing' THEN 'JOURNAL_ENTRY_TESTING'
                WHEN 'revenue_testing' THEN 'REVENUE_TESTING'
                WHEN 'procurement_testing' THEN 'PROCUREMENT_TESTING'
                ELSE NULL
            END
            WHERE amc.id IS NOT NULL
            """
        )
    ).fetchall()

    if rows:
        table = sa.table(
            "engagement_enabled_modules",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("engagement_id", postgresql.UUID(as_uuid=True)),
            sa.column("module_catalog_id", postgresql.UUID(as_uuid=True)),
            sa.column("is_enabled", sa.Boolean),
        )
        op.bulk_insert(
            table,
            [
                {
                    "id": uuid.uuid4(),
                    "engagement_id": row[0],
                    "module_catalog_id": row[2],
                    "is_enabled": True,
                }
                for row in rows
            ],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_engagement_enabled_modules_engagement_id",
        table_name="engagement_enabled_modules",
    )
    op.drop_table("engagement_enabled_modules")
