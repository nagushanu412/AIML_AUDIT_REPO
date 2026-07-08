"""Backfill organization_id on legacy clients and engagements

Revision ID: 020
Revises: 019
Create Date: 2026-06-30

Links legacy engagements to organizations via client or owner membership.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE clients c
        SET organization_id = om.organization_id
        FROM organization_members om
        WHERE c.organization_id IS NULL
          AND c.user_id = om.user_id
          AND om.status IN ('active', 'invited')
        """
    )
    op.execute(
        """
        UPDATE audit_engagements ae
        SET organization_id = c.organization_id
        FROM clients c
        WHERE ae.client_id = c.id
          AND ae.organization_id IS NULL
          AND c.organization_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE audit_engagements ae
        SET organization_id = om.organization_id
        FROM clients c
        JOIN organization_members om ON om.user_id = c.user_id
        WHERE ae.client_id = c.id
          AND ae.organization_id IS NULL
          AND c.organization_id IS NULL
          AND om.status IN ('active', 'invited')
        """
    )


def downgrade() -> None:
    pass
