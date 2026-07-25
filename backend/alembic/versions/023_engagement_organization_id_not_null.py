"""Remediation M1 Step 1 — audit_engagements.organization_id NOT NULL

Revision ID: 023
Revises: 022
Create Date: 2026-07-25

Backfill remaining nulls from client/org membership, assign true orphans to a
recovery organization, then enforce NOT NULL.
Does not introduce PostgreSQL RLS (deferred per ADR-003).
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Backfill from client.organization_id
    op.execute(
        sa.text(
            """
            UPDATE audit_engagements ae
            SET organization_id = c.organization_id
            FROM clients c
            WHERE ae.client_id = c.id
              AND ae.organization_id IS NULL
              AND c.organization_id IS NOT NULL
            """
        )
    )
    # 2) Backfill via client's organization membership
    op.execute(
        sa.text(
            """
            UPDATE audit_engagements ae
            SET organization_id = om.organization_id
            FROM clients c
            JOIN organization_members om ON om.user_id = c.user_id
            WHERE ae.client_id = c.id
              AND ae.organization_id IS NULL
              AND om.status IN ('active', 'invited')
            """
        )
    )
    # 3) Backfill via client's user default organization
    op.execute(
        sa.text(
            """
            UPDATE audit_engagements ae
            SET organization_id = u.default_organization_id
            FROM clients c
            JOIN users u ON u.id = c.user_id
            WHERE ae.client_id = c.id
              AND ae.organization_id IS NULL
              AND u.default_organization_id IS NOT NULL
            """
        )
    )

    conn = op.get_bind()
    remaining = int(
        conn.execute(
            sa.text(
                "SELECT count(*) FROM audit_engagements WHERE organization_id IS NULL"
            )
        ).scalar()
        or 0
    )

    # 4) True orphans: attach to a dedicated recovery organization (and backfill client)
    if remaining > 0:
        recovery_org_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO organizations (id, name, slug, status, settings)
                VALUES (
                    :id,
                    'Legacy Data Recovery',
                    :slug,
                    'active',
                    '{}'::jsonb
                )
                """
            ),
            {"id": str(recovery_org_id), "slug": f"legacy-recovery-{recovery_org_id.hex[:8]}"},
        )
        conn.execute(
            sa.text(
                """
                UPDATE clients c
                SET organization_id = :org_id
                FROM audit_engagements ae
                WHERE ae.client_id = c.id
                  AND ae.organization_id IS NULL
                  AND c.organization_id IS NULL
                """
            ),
            {"org_id": str(recovery_org_id)},
        )
        conn.execute(
            sa.text(
                """
                UPDATE audit_engagements
                SET organization_id = :org_id
                WHERE organization_id IS NULL
                """
            ),
            {"org_id": str(recovery_org_id)},
        )

    remaining_after = int(
        conn.execute(
            sa.text(
                "SELECT count(*) FROM audit_engagements WHERE organization_id IS NULL"
            )
        ).scalar()
        or 0
    )
    if remaining_after > 0:
        raise RuntimeError(
            f"Cannot set audit_engagements.organization_id NOT NULL: "
            f"{remaining_after} row(s) still have NULL organization_id after backfill."
        )

    op.alter_column(
        "audit_engagements",
        "organization_id",
        existing_type=sa.UUID(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "audit_engagements",
        "organization_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
