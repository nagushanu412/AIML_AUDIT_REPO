"""Workpapers, evidence, and evidence links

Revision ID: 015
Revises: 014
Create Date: 2026-06-07

Phase 2 Milestone 2 — Workpapers & Evidence Repository.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("root_evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="other"),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
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
            "category IN ("
            "'invoice', 'contract', 'correspondence', 'bank_statement', "
            "'screenshot', 'spreadsheet', 'report', 'other'"
            ")",
            name="ck_evidence_category",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_evidence_status",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["audit_projects.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["root_evidence_id"], ["evidence.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_engagement_id", "evidence", ["engagement_id"])
    op.create_index("ix_evidence_project_id", "evidence", ["project_id"])
    op.create_index("ix_evidence_root_current", "evidence", ["root_evidence_id", "is_current"])
    op.create_index("ix_evidence_file_hash", "evidence", ["file_hash"])

    op.create_table(
        "workpapers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("root_workpaper_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reference_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="testing"),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
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
            "category IN ("
            "'planning', 'risk_assessment', 'testing', 'sampling', "
            "'completion', 'other'"
            ")",
            name="ck_workpapers_category",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'final', 'archived')",
            name="ck_workpapers_status",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["audit_projects.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["root_workpaper_id"], ["workpapers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "engagement_id",
            "reference_code",
            "version_number",
            name="uq_workpapers_engagement_ref_version",
        ),
    )
    op.create_index("ix_workpapers_engagement_id", "workpapers", ["engagement_id"])
    op.create_index("ix_workpapers_project_id", "workpapers", ["project_id"])
    op.create_index(
        "ix_workpapers_root_current", "workpapers", ["root_workpaper_id", "is_current"]
    )

    op.create_table(
        "evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workpaper_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("linked_entity_type", sa.String(length=50), nullable=False),
        sa.Column("linked_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_type", sa.String(length=50), nullable=False, server_default="reference"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "linked_entity_type IN ('finding', 'workpaper', 'journal_entry', 'transaction')",
            name="ck_evidence_links_entity_type",
        ),
        sa.CheckConstraint(
            "link_type IN ('supports', 'references', 'attachment')",
            name="ck_evidence_links_link_type",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["audit_engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"], ["audit_findings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workpaper_id"], ["workpapers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evidence_id",
            "linked_entity_type",
            "linked_entity_id",
            name="uq_evidence_links_entity",
        ),
    )
    op.create_index("ix_evidence_links_evidence_id", "evidence_links", ["evidence_id"])
    op.create_index("ix_evidence_links_finding_id", "evidence_links", ["finding_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_links_finding_id", table_name="evidence_links")
    op.drop_index("ix_evidence_links_evidence_id", table_name="evidence_links")
    op.drop_table("evidence_links")
    op.drop_index("ix_workpapers_root_current", table_name="workpapers")
    op.drop_index("ix_workpapers_project_id", table_name="workpapers")
    op.drop_index("ix_workpapers_engagement_id", table_name="workpapers")
    op.drop_table("workpapers")
    op.drop_index("ix_evidence_file_hash", table_name="evidence")
    op.drop_index("ix_evidence_root_current", table_name="evidence")
    op.drop_index("ix_evidence_project_id", table_name="evidence")
    op.drop_index("ix_evidence_engagement_id", table_name="evidence")
    op.drop_table("evidence")
