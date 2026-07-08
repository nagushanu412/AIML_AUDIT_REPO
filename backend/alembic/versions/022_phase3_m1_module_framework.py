"""Phase 3 M1 — Generic Module Framework tables

Revision ID: 022
Revises: 021
Create Date: 2026-07-08
"""
from __future__ import annotations

import json
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BUILT_MODULES = (
    {
        "code": "JOURNAL_ENTRY_TESTING",
        "project_type": "journal_testing",
        "rule_prefix": "",
        "input_format": "xlsx",
        "theme_color": "blue",
        "ui_config": {"stepper_steps": 6, "accent": "blue"},
    },
    {
        "code": "REVENUE_TESTING",
        "project_type": "revenue_testing",
        "rule_prefix": "REV_",
        "input_format": "xlsx",
        "theme_color": "indigo",
        "ui_config": {"stepper_steps": 6, "accent": "indigo"},
    },
    {
        "code": "PROCUREMENT_TESTING",
        "project_type": "procurement_testing",
        "rule_prefix": "PROC_",
        "input_format": "xlsx",
        "theme_color": "emerald",
        "ui_config": {"stepper_steps": 6, "accent": "emerald"},
    },
)


def upgrade() -> None:
    op.add_column(
        "audit_module_catalog",
        sa.Column("project_type", sa.String(50), nullable=True),
    )
    op.add_column(
        "audit_module_catalog",
        sa.Column("rule_prefix", sa.String(20), nullable=True),
    )
    op.add_column(
        "audit_module_catalog",
        sa.Column("input_format", sa.String(20), nullable=True, server_default="xlsx"),
    )
    op.add_column(
        "audit_module_catalog",
        sa.Column("theme_color", sa.String(30), nullable=True),
    )
    op.add_column(
        "audit_module_catalog",
        sa.Column(
            "ui_config",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )

    op.add_column(
        "module_analysis_runs",
        sa.Column("pipeline_step", sa.String(50), nullable=True),
    )
    op.add_column(
        "module_analysis_runs",
        sa.Column("error_detail", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "module_plugin_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_code", sa.String(50), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["module_code"],
            ["audit_module_catalog.code"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_code", name="uq_module_plugin_config_code"),
    )
    op.create_index(
        "ix_module_plugin_config_module_code",
        "module_plugin_config",
        ["module_code"],
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flag_key", sa.String(100), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("module_code", sa.String(50), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "flag_key",
            "organization_id",
            "module_code",
            name="uq_feature_flags_scope",
        ),
    )
    op.create_index("ix_feature_flags_flag_key", "feature_flags", ["flag_key"])

    conn = op.get_bind()
    for row in BUILT_MODULES:
        conn.execute(
            sa.text(
                """
                UPDATE audit_module_catalog
                SET project_type = :project_type,
                    rule_prefix = :rule_prefix,
                    input_format = :input_format,
                    theme_color = :theme_color,
                    ui_config = CAST(:ui_config AS jsonb)
                WHERE code = :code
                """
            ),
            {
                "code": row["code"],
                "project_type": row["project_type"],
                "rule_prefix": row["rule_prefix"],
                "input_format": row["input_format"],
                "theme_color": row["theme_color"],
                "ui_config": json.dumps(row["ui_config"]),
            },
        )

    from app.services.module_framework.plugin_config_seed import PLUGIN_CONFIG_SEED

    config_table = sa.table(
        "module_plugin_config",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("module_code", sa.String),
        sa.column("version", sa.String),
        sa.column("config", postgresql.JSONB),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        config_table,
        [
            {
                "id": uuid.uuid4(),
                "module_code": row["module_code"],
                "version": row.get("version", "1.0.0"),
                "config": row["config"],
                "is_active": True,
            }
            for row in PLUGIN_CONFIG_SEED
        ],
    )

    op.bulk_insert(
        sa.table(
            "feature_flags",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("flag_key", sa.String),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("module_code", sa.String),
            sa.column("is_enabled", sa.Boolean),
            sa.column("config", postgresql.JSONB),
        ),
        [
            {
                "id": uuid.uuid4(),
                "flag_key": "generic_module_api",
                "organization_id": None,
                "module_code": None,
                "is_enabled": True,
                "config": {},
            },
            {
                "id": uuid.uuid4(),
                "flag_key": "analysis_engine_v2",
                "organization_id": None,
                "module_code": None,
                "is_enabled": True,
                "config": {},
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_feature_flags_flag_key", table_name="feature_flags")
    op.drop_table("feature_flags")
    op.drop_index("ix_module_plugin_config_module_code", table_name="module_plugin_config")
    op.drop_table("module_plugin_config")
    op.drop_column("module_analysis_runs", "error_detail")
    op.drop_column("module_analysis_runs", "pipeline_step")
    op.drop_column("audit_module_catalog", "ui_config")
    op.drop_column("audit_module_catalog", "theme_color")
    op.drop_column("audit_module_catalog", "input_format")
    op.drop_column("audit_module_catalog", "rule_prefix")
    op.drop_column("audit_module_catalog", "project_type")
