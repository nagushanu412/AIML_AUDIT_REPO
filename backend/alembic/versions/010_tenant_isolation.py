"""Tenant isolation — organization_id on clients and engagements

Revision ID: 010
Revises: 009
Create Date: 2026-06-07

Milestone 4 — Tenant Isolation.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "audit_engagements",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_clients_organization_id",
        "clients",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_audit_engagements_organization_id",
        "audit_engagements",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_clients_organization_id", "clients", ["organization_id"])
    op.create_index(
        "ix_audit_engagements_organization_id",
        "audit_engagements",
        ["organization_id"],
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE clients c
            SET organization_id = u.default_organization_id
            FROM users u
            WHERE c.user_id = u.id
              AND u.default_organization_id IS NOT NULL
              AND c.organization_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE audit_engagements ae
            SET organization_id = c.organization_id
            FROM clients c
            WHERE ae.client_id = c.id
              AND c.organization_id IS NOT NULL
              AND ae.organization_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_audit_engagements_organization_id", table_name="audit_engagements")
    op.drop_index("ix_clients_organization_id", table_name="clients")
    op.drop_constraint(
        "fk_audit_engagements_organization_id",
        "audit_engagements",
        type_="foreignkey",
    )
    op.drop_constraint("fk_clients_organization_id", "clients", type_="foreignkey")
    op.drop_column("audit_engagements", "organization_id")
    op.drop_column("clients", "organization_id")
