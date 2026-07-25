"""Remediation M1 Step 2 — denormalize organization_id on tenant tables

Revision ID: 024
Revises: 023
Create Date: 2026-07-25

Adds / backfills / enforces NOT NULL organization_id on every tenant-scoped
table listed in Remediation Plan §0.2. Does not introduce PostgreSQL RLS.
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADD_COLUMN_TABLES = (
    "journal_entries",
    "revenue_invoices",
    "procurement_invoices",
    "audit_findings",
    "rule_results",
    "revenue_rule_results",
    "procurement_rule_results",
    "risk_scores",
    "revenue_risk_scores",
    "procurement_risk_scores",
    "reports",
    "evidence_links",
    "engagement_enabled_modules",
    "engagement_team_members",
    "review_comments",
    "approvals",
)

PROJECT_SCOPED = (
    "journal_entries",
    "revenue_invoices",
    "procurement_invoices",
    "audit_findings",
    "rule_results",
    "revenue_rule_results",
    "procurement_rule_results",
    "risk_scores",
    "revenue_risk_scores",
    "procurement_risk_scores",
    "reports",
)

ENGAGEMENT_SCOPED = (
    "evidence_links",
    "engagement_enabled_modules",
    "review_comments",
    "approvals",
    "evidence",
    "workpapers",
    "finding_relationships",
    "module_analysis_runs",
)

EXISTING_NULLABLE = (
    "evidence",
    "workpapers",
    "audit_logs",
    "feature_flags",
    "finding_relationships",
    "module_analysis_runs",
)

ALL_NOT_NULL = ADD_COLUMN_TABLES + EXISTING_NULLABLE

FK_RECREATE = (
    ("evidence", "evidence_organization_id_fkey"),
    ("workpapers", "workpapers_organization_id_fkey"),
    ("audit_logs", "audit_logs_organization_id_fkey"),
    ("finding_relationships", "finding_relationships_organization_id_fkey"),
    ("module_analysis_runs", "module_analysis_runs_organization_id_fkey"),
)


def _backfill_from_project(table: str) -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE {table} t
            SET organization_id = e.organization_id
            FROM audit_projects p
            JOIN audit_engagements e ON e.id = p.engagement_id
            WHERE t.project_id = p.id
              AND t.organization_id IS NULL
            """
        )
    )


def _backfill_from_engagement(table: str) -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE {table} t
            SET organization_id = e.organization_id
            FROM audit_engagements e
            WHERE t.engagement_id = e.id
              AND t.organization_id IS NULL
            """
        )
    )


def upgrade() -> None:
    for table in ADD_COLUMN_TABLES:
        op.add_column(
            table,
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )
        op.create_foreign_key(
            f"fk_{table}_organization_id",
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])

    for table in PROJECT_SCOPED:
        _backfill_from_project(table)

    for table in ENGAGEMENT_SCOPED:
        _backfill_from_engagement(table)

    # engagement_team_members: prefer organization_members path (plan note)
    op.execute(
        sa.text(
            """
            UPDATE engagement_team_members etm
            SET organization_id = om.organization_id
            FROM organization_members om
            WHERE etm.organization_member_id = om.id
              AND etm.organization_id IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE engagement_team_members etm
            SET organization_id = e.organization_id
            FROM audit_engagements e
            WHERE etm.engagement_id = e.id
              AND etm.organization_id IS NULL
            """
        )
    )

    # audit_logs: no engagement/project FK — backfill from user
    op.execute(
        sa.text(
            """
            UPDATE audit_logs al
            SET organization_id = u.default_organization_id
            FROM users u
            WHERE al.user_id = u.id
              AND al.organization_id IS NULL
              AND u.default_organization_id IS NOT NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE audit_logs al
            SET organization_id = om.organization_id
            FROM organization_members om
            WHERE al.user_id = om.user_id
              AND al.organization_id IS NULL
              AND om.status IN ('active', 'invited')
            """
        )
    )

    # feature_flags: global (NULL org) rows → dedicated platform organization
    conn = op.get_bind()
    global_flags = int(
        conn.execute(
            sa.text(
                "SELECT count(*) FROM feature_flags WHERE organization_id IS NULL"
            )
        ).scalar()
        or 0
    )
    if global_flags > 0:
        platform_org_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO organizations (id, name, slug, status, settings)
                VALUES (
                    :id,
                    'Platform Global Flags',
                    :slug,
                    'active',
                    '{}'::jsonb
                )
                """
            ),
            {
                "id": str(platform_org_id),
                "slug": f"platform-global-flags-{platform_org_id.hex[:8]}",
            },
        )
        conn.execute(
            sa.text(
                """
                UPDATE feature_flags
                SET organization_id = :org_id
                WHERE organization_id IS NULL
                """
            ),
            {"org_id": str(platform_org_id)},
        )

    # Remaining audit_logs orphans → same platform org if still null
    remaining_logs = int(
        conn.execute(
            sa.text("SELECT count(*) FROM audit_logs WHERE organization_id IS NULL")
        ).scalar()
        or 0
    )
    if remaining_logs > 0:
        platform = conn.execute(
            sa.text(
                """
                SELECT id FROM organizations
                WHERE slug LIKE 'platform-global-flags-%'
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
        ).scalar()
        if platform is None:
            platform_org_id = uuid.uuid4()
            conn.execute(
                sa.text(
                    """
                    INSERT INTO organizations (id, name, slug, status, settings)
                    VALUES (
                        :id,
                        'Platform Global Flags',
                        :slug,
                        'active',
                        '{}'::jsonb
                    )
                    """
                ),
                {
                    "id": str(platform_org_id),
                    "slug": f"platform-global-flags-{platform_org_id.hex[:8]}",
                },
            )
            platform = platform_org_id
        conn.execute(
            sa.text(
                """
                UPDATE audit_logs
                SET organization_id = :org_id
                WHERE organization_id IS NULL
                """
            ),
            {"org_id": str(platform)},
        )

    for table in ALL_NOT_NULL:
        remaining = int(
            conn.execute(
                sa.text(
                    f"SELECT count(*) FROM {table} WHERE organization_id IS NULL"
                )
            ).scalar()
            or 0
        )
        if remaining > 0:
            raise RuntimeError(
                f"Cannot set {table}.organization_id NOT NULL: "
                f"{remaining} row(s) still NULL after backfill."
            )

    # Tighten existing SET NULL FKs before NOT NULL
    for table, fk_name in FK_RECREATE:
        op.drop_constraint(fk_name, table, type_="foreignkey")
        op.create_foreign_key(
            fk_name,
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )

    for table in ALL_NOT_NULL:
        op.alter_column(
            table,
            "organization_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False,
        )


def downgrade() -> None:
    for table in ALL_NOT_NULL:
        op.alter_column(
            table,
            "organization_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=True,
        )

    for table, fk_name in FK_RECREATE:
        op.drop_constraint(fk_name, table, type_="foreignkey")
        op.create_foreign_key(
            fk_name,
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="SET NULL",
        )

    for table in ADD_COLUMN_TABLES:
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        op.drop_constraint(f"fk_{table}_organization_id", table, type_="foreignkey")
        op.drop_column(table, "organization_id")
