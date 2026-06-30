"""Engagement team members and assignment history

Revision ID: 014
Revises: 013
Create Date: 2026-06-07

Phase 2 Milestone 1 — Engagement Team Management.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engagement_team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
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
            "role IN ('partner', 'audit_manager', 'senior_auditor', 'auditor', 'reviewer')",
            name="ck_engagement_team_members_role",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'removed')",
            name="ck_engagement_team_members_status",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_member_id"],
            ["organization_members.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "engagement_id",
            "user_id",
            name="uq_engagement_team_members_engagement_user",
        ),
    )
    op.create_index(
        "ix_engagement_team_members_engagement_id",
        "engagement_team_members",
        ["engagement_id"],
    )
    op.create_index(
        "ix_engagement_team_members_user_id",
        "engagement_team_members",
        ["user_id"],
    )
    op.create_index(
        "ix_engagement_team_members_role_status",
        "engagement_team_members",
        ["engagement_id", "role", "status"],
    )

    op.create_table(
        "engagement_team_assignment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("previous_role", sa.String(length=50), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('assigned', 'role_changed', 'removed', 'reactivated')",
            name="ck_engagement_team_history_action",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["team_member_id"],
            ["engagement_team_members.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_engagement_team_history_engagement_id",
        "engagement_team_assignment_history",
        ["engagement_id"],
    )
    op.create_index(
        "ix_engagement_team_history_created_at",
        "engagement_team_assignment_history",
        ["engagement_id", "created_at"],
    )
    op.create_index(
        "ix_engagement_team_history_user_id",
        "engagement_team_assignment_history",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_engagement_team_history_user_id",
        table_name="engagement_team_assignment_history",
    )
    op.drop_index(
        "ix_engagement_team_history_created_at",
        table_name="engagement_team_assignment_history",
    )
    op.drop_index(
        "ix_engagement_team_history_engagement_id",
        table_name="engagement_team_assignment_history",
    )
    op.drop_table("engagement_team_assignment_history")
    op.drop_index(
        "ix_engagement_team_members_role_status",
        table_name="engagement_team_members",
    )
    op.drop_index(
        "ix_engagement_team_members_user_id",
        table_name="engagement_team_members",
    )
    op.drop_index(
        "ix_engagement_team_members_engagement_id",
        table_name="engagement_team_members",
    )
    op.drop_table("engagement_team_members")
