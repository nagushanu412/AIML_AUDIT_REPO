"""Organizations table and user default organization link

Revision ID: 007
Revises: 006
Create Date: 2026-06-07

Milestone 1 — Organizations only (no organization_members yet).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORGANIZATION_STATUSES = ("active", "suspended", "closed")


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
            f"status IN {ORGANIZATION_STATUSES}",
            name="ck_organizations_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_status", "organizations", ["status"])

    op.add_column(
        "users",
        sa.Column("default_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_default_organization_id",
        "users",
        "organizations",
        ["default_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_users_default_organization_id",
        "users",
        ["default_organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_default_organization_id", table_name="users")
    op.drop_constraint("fk_users_default_organization_id", "users", type_="foreignkey")
    op.drop_column("users", "default_organization_id")
    op.drop_index("ix_organizations_status", table_name="organizations")
    op.drop_table("organizations")
