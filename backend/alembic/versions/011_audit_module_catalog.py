"""Audit module catalog

Revision ID: 011
Revises: 010
Create Date: 2026-06-07

Milestone 5 — Audit Module Catalog (22 modules).
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUSES = ("built", "beta", "planned")


def upgrade() -> None:
    op.create_table(
        "audit_module_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(50), nullable=False, server_default="BookOpen"),
        sa.Column("implementation_status", sa.String(50), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
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
            f"implementation_status IN {STATUSES}",
            name="ck_audit_module_catalog_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_audit_module_catalog_code"),
        sa.UniqueConstraint("slug", name="uq_audit_module_catalog_slug"),
    )
    op.create_index(
        "ix_audit_module_catalog_display_order",
        "audit_module_catalog",
        ["display_order"],
    )

    from app.services.module_catalog_constants import MODULE_CATALOG_SEED

    table = sa.table(
        "audit_module_catalog",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("slug", sa.String),
        sa.column("icon", sa.String),
        sa.column("implementation_status", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("metadata", postgresql.JSONB),
    )
    op.bulk_insert(
        table,
        [
            {
                "id": uuid.uuid4(),
                "is_active": True,
                "metadata": {},
                **row,
            }
            for row in MODULE_CATALOG_SEED
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_module_catalog_display_order", table_name="audit_module_catalog")
    op.drop_table("audit_module_catalog")
