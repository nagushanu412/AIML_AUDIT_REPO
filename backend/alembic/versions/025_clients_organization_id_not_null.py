"""Remediation M1 follow-up — clients.organization_id NOT NULL

Revision ID: 025
Revises: 024
Create Date: 2026-07-25

Backfill any remaining nulls, then enforce NOT NULL.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) From owning user's default organization
    op.execute(
        sa.text(
            """
            UPDATE clients c
            SET organization_id = u.default_organization_id
            FROM users u
            WHERE c.user_id = u.id
              AND c.organization_id IS NULL
              AND u.default_organization_id IS NOT NULL
            """
        )
    )
    # 2) From organization membership
    op.execute(
        sa.text(
            """
            UPDATE clients c
            SET organization_id = om.organization_id
            FROM organization_members om
            WHERE c.user_id = om.user_id
              AND c.organization_id IS NULL
              AND om.status IN ('active', 'invited')
            """
        )
    )
    # 3) From any engagement already linked to the client
    op.execute(
        sa.text(
            """
            UPDATE clients c
            SET organization_id = e.organization_id
            FROM audit_engagements e
            WHERE e.client_id = c.id
              AND c.organization_id IS NULL
              AND e.organization_id IS NOT NULL
            """
        )
    )

    conn = op.get_bind()
    remaining = int(
        conn.execute(
            sa.text("SELECT count(*) FROM clients WHERE organization_id IS NULL")
        ).scalar()
        or 0
    )
    if remaining > 0:
        raise RuntimeError(
            f"Cannot set clients.organization_id NOT NULL: "
            f"{remaining} row(s) still have NULL organization_id after backfill."
        )

    op.alter_column(
        "clients",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "clients",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
