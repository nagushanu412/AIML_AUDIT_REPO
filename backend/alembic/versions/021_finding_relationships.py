"""Cross-module finding relationships (Phase 2).

Revision ID: 021
Revises: 020
Create Date: 2026-07-08
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finding_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "engagement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_engagements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "source_finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "relationship_type IN ("
            "'related', 'supports', 'contradicts', 'duplicate_of', "
            "'root_cause', 'adjustment_impact'"
            ")",
            name="ck_finding_relationships_type",
        ),
        sa.UniqueConstraint(
            "source_finding_id",
            "target_finding_id",
            "relationship_type",
            name="uq_finding_relationships_pair_type",
        ),
    )
    op.create_index(
        "ix_finding_relationships_engagement_id",
        "finding_relationships",
        ["engagement_id"],
    )
    op.create_index(
        "ix_finding_relationships_source_finding_id",
        "finding_relationships",
        ["source_finding_id"],
    )
    op.create_index(
        "ix_finding_relationships_target_finding_id",
        "finding_relationships",
        ["target_finding_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_finding_relationships_target_finding_id",
        table_name="finding_relationships",
    )
    op.drop_index(
        "ix_finding_relationships_source_finding_id",
        table_name="finding_relationships",
    )
    op.drop_index(
        "ix_finding_relationships_engagement_id",
        table_name="finding_relationships",
    )
    op.drop_table("finding_relationships")
