"""Organization members and RBAC foundation

Revision ID: 009
Revises: 008
Create Date: 2026-06-28

Milestone 3 — Organization Members.
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MEMBER_ROLES = (
    "organization_owner",
    "partner",
    "audit_manager",
    "senior_auditor",
    "auditor",
    "reviewer",
    "client_user",
    "read_only",
)

MEMBER_STATUSES = ("active", "invited", "disabled")


def upgrade() -> None:
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
            f"role IN {MEMBER_ROLES}",
            name="ck_organization_members_role",
        ),
        sa.CheckConstraint(
            f"status IN {MEMBER_STATUSES}",
            name="ck_organization_members_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_members_org_user",
        ),
    )
    op.create_index(
        "ix_organization_members_organization_id",
        "organization_members",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_members_user_id",
        "organization_members",
        ["user_id"],
    )
    op.create_index(
        "ix_organization_members_status",
        "organization_members",
        ["status"],
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT u.id, u.default_organization_id
            FROM users u
            WHERE u.default_organization_id IS NOT NULL
            """
        )
    ).fetchall()

    if rows:
        members_table = sa.table(
            "organization_members",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("user_id", postgresql.UUID(as_uuid=True)),
            sa.column("role", sa.String),
            sa.column("status", sa.String),
        )
        op.bulk_insert(
            members_table,
            [
                {
                    "id": uuid.uuid4(),
                    "organization_id": row[1],
                    "user_id": row[0],
                    "role": "organization_owner",
                    "status": "active",
                }
                for row in rows
            ],
        )


def downgrade() -> None:
    op.drop_index("ix_organization_members_status", table_name="organization_members")
    op.drop_index("ix_organization_members_user_id", table_name="organization_members")
    op.drop_index(
        "ix_organization_members_organization_id",
        table_name="organization_members",
    )
    op.drop_table("organization_members")
