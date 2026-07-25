"""Remediation M3 Step 2 — backfill audit_findings.reviewed_by / reviewed_at

Revision ID: 028
Revises: 027
Create Date: 2026-07-25

For findings already in a decision status (not open / under_review) with
reviewed_at IS NULL:

1. Prefer latest finding_status_history row where new_status matches current
   status and action IN ('status_change', 'reopened') → changed_by / created_at.
2. Else fall back to updated_by / updated_at when both are present
   (approximation — not a guaranteed decision stamp).
3. Else leave reviewed_* null (do not invent values).
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE audit_findings AS f
        SET
            reviewed_by = COALESCE(hist.changed_by, f.updated_by),
            reviewed_at = COALESCE(hist.created_at, f.updated_at)
        FROM (
            SELECT DISTINCT ON (h.finding_id)
                h.finding_id,
                h.changed_by,
                h.created_at
            FROM finding_status_history h
            JOIN audit_findings f2 ON f2.id = h.finding_id
            WHERE f2.status NOT IN ('open', 'under_review')
              AND f2.reviewed_at IS NULL
              AND h.new_status = f2.status
              AND h.action IN ('status_change', 'reopened')
            ORDER BY h.finding_id, h.created_at DESC
        ) AS hist
        WHERE f.id = hist.finding_id
          AND f.status NOT IN ('open', 'under_review')
          AND f.reviewed_at IS NULL
        """
    )
    # Fallback: updated_by / updated_at when history did not supply a stamp.
    op.execute(
        """
        UPDATE audit_findings
        SET
            reviewed_by = updated_by,
            reviewed_at = updated_at
        WHERE status NOT IN ('open', 'under_review')
          AND reviewed_at IS NULL
          AND updated_by IS NOT NULL
          AND updated_at IS NOT NULL
        """
    )


def downgrade() -> None:
    # Cannot distinguish backfilled stamps from post-027 live stamps; no-op.
    pass
