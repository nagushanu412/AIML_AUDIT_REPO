"""Remediation M4 Step 3 — rule content versioning

Revision ID: 030
Revises: 029
Create Date: 2026-07-25

Named rule_content_version (not version) to avoid collision with
module_plugin_config.version (plugin code version).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rules_master",
        sa.Column(
            "rule_content_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "audit_findings",
        sa.Column("rule_content_version", sa.Integer(), nullable=True),
    )
    # Existing rules keep DEFAULT 1; drop server_default so ORM default owns inserts.
    op.alter_column("rules_master", "rule_content_version", server_default=None)


def downgrade() -> None:
    op.drop_column("audit_findings", "rule_content_version")
    op.drop_column("rules_master", "rule_content_version")
