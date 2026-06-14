"""Add clients, engagements, rules_master, reports; refactor audit_projects hierarchy

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100)),
        sa.Column("gstin", sa.String(50)),
        sa.Column("pan", sa.String(20)),
        sa.Column("contact_person", sa.String(255)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clients_user_id", "clients", ["user_id"])

    op.create_table(
        "audit_engagements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.String(20), nullable=False),
        sa.Column("audit_type", sa.String(50), server_default="Statutory", nullable=False),
        sa.Column("status", sa.String(50), server_default="planned", nullable=False),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("financial_year_end", sa.Date(), nullable=False),
        sa.Column("large_value_threshold", sa.Numeric(18, 2), server_default="100000.00", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_engagements_client_id", "audit_engagements", ["client_id"])

    op.create_table(
        "rules_master",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_code", sa.String(50), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("default_score", sa.Integer(), server_default="10", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("config_schema", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text()),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(50), server_default="ready", nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["audit_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_project_id", "reports", ["project_id"])

    op.add_column("audit_projects", sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "audit_projects",
        sa.Column("project_type", sa.String(100), server_default="journal_testing", nullable=True),
    )
    op.add_column("rule_results", sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_rule_results_rule_id", "rule_results", "rules_master", ["rule_id"], ["id"], ondelete="SET NULL"
    )

    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO rules_master (id, rule_code, rule_name, description, default_score, is_active)
        VALUES
            (gen_random_uuid(), 'LARGE_VALUE', 'Large Value Entries',
             'Flag entries greater than configurable threshold.', 20, true),
            (gen_random_uuid(), 'YEAR_END', 'Year End Entries',
             'Flag entries in last 7 days of financial year.', 15, true),
            (gen_random_uuid(), 'ROUND_AMOUNT', 'Round Amount Entries',
             'Flag round figure amounts.', 10, true),
            (gen_random_uuid(), 'WEEKEND', 'Weekend Entries',
             'Flag weekend postings.', 10, true),
            (gen_random_uuid(), 'SUSPENSE_ACCOUNT', 'Suspense Account Entries',
             'Flag suspense/clearing/adjustment accounts.', 20, true),
            (gen_random_uuid(), 'MANUAL_JOURNAL', 'Manual Journal Entries',
             'Flag manual adjustments in description.', 15, true),
            (gen_random_uuid(), 'UNUSUAL_POSTING', 'Unusual Posting Patterns',
             'Flag users with unusually high posting volume.', 10, true)
        ON CONFLICT (rule_code) DO NOTHING
    """))

    conn.execute(sa.text("""
        UPDATE rule_results rr
        SET rule_id = rm.id
        FROM rules_master rm
        WHERE rr.rule_code = rm.rule_code AND rr.rule_id IS NULL
    """))

    conn.execute(sa.text("""
        DO $$
        DECLARE
            r RECORD;
            v_client_id UUID;
            v_engagement_id UUID;
        BEGIN
            FOR r IN SELECT * FROM audit_projects LOOP
                INSERT INTO clients (id, user_id, name, status, created_at, updated_at)
                VALUES (
                    gen_random_uuid(),
                    r.user_id,
                    COALESCE(r.client_name, 'Migrated Client'),
                    'active',
                    NOW(),
                    NOW()
                )
                RETURNING id INTO v_client_id;

                INSERT INTO audit_engagements (
                    id, client_id, financial_year, audit_type, status,
                    financial_year_end, large_value_threshold, created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    v_client_id,
                    'FY 2024-25',
                    'Statutory',
                    'active',
                    r.financial_year_end,
                    r.large_value_threshold,
                    NOW(),
                    NOW()
                )
                RETURNING id INTO v_engagement_id;

                UPDATE audit_projects
                SET engagement_id = v_engagement_id,
                    project_type = 'journal_testing'
                WHERE id = r.id;
            END LOOP;
        END $$;
    """))

    op.alter_column("audit_projects", "engagement_id", nullable=False)
    op.alter_column("audit_projects", "project_type", nullable=False)
    op.create_foreign_key(
        "fk_audit_projects_engagement_id",
        "audit_projects",
        "audit_engagements",
        ["engagement_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_audit_projects_engagement_id", "audit_projects", ["engagement_id"])

    op.drop_index("ix_audit_projects_user_id", table_name="audit_projects")
    op.drop_constraint("audit_projects_user_id_fkey", "audit_projects", type_="foreignkey")
    op.drop_column("audit_projects", "user_id")
    op.drop_column("audit_projects", "client_name")
    op.drop_column("audit_projects", "financial_year_end")
    op.drop_column("audit_projects", "large_value_threshold")


def downgrade() -> None:
    op.add_column("audit_projects", sa.Column("large_value_threshold", sa.Numeric(18, 2), server_default="100000"))
    op.add_column("audit_projects", sa.Column("financial_year_end", sa.Date(), nullable=True))
    op.add_column("audit_projects", sa.Column("client_name", sa.String(255)))
    op.add_column("audit_projects", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.drop_constraint("fk_rule_results_rule_id", "rule_results", type_="foreignkey")
    op.drop_column("rule_results", "rule_id")

    op.drop_index("ix_reports_project_id", table_name="reports")
    op.drop_table("reports")
    op.drop_table("rules_master")
    op.drop_index("ix_audit_engagements_client_id", table_name="audit_engagements")
    op.drop_table("audit_engagements")
    op.drop_index("ix_clients_user_id", table_name="clients")
    op.drop_table("clients")
