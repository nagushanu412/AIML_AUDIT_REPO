"""Seed default config_schema for all rules_master rows

Revision ID: 004
Revises: 003
Create Date: 2026-06-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CONFIGS = {
    "LARGE_VALUE": {"threshold": None},
    "YEAR_END": {"days_before": 7},
    "ROUND_AMOUNT": {"suffixes": [500, 1000, 5000]},
    "WEEKEND": {"weekdays": [5, 6]},
    "SUSPENSE_ACCOUNT": {"keywords": ["suspense", "clearing", "adjustment"]},
    "MANUAL_JOURNAL": {"keywords": ["manual", "adjustment", "correction"]},
    "UNUSUAL_POSTING": {"std_multiplier": 2, "min_count": 5},
}


def upgrade() -> None:
    conn = op.get_bind()
    for rule_code, config in DEFAULT_CONFIGS.items():
        import json

        conn.execute(
            sa.text(
                """
                UPDATE rules_master
                SET config_schema = CAST(:config AS jsonb)
                WHERE rule_code = :rule_code
                  AND (config_schema IS NULL OR config_schema = '{}'::jsonb)
                """
            ),
            {"rule_code": rule_code, "config": json.dumps(config)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE rules_master SET config_schema = '{}'::jsonb"))
