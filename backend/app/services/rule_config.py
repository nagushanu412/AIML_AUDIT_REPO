"""Default and merged per-rule configuration for the journal entry engine."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.audit import RuleMaster

DEFAULT_RULE_CONFIGS: dict[str, dict[str, Any]] = {
    "LARGE_VALUE": {"threshold": None},
    "YEAR_END": {"days_before": 7},
    "ROUND_AMOUNT": {"suffixes": [500, 1000, 5000]},
    "WEEKEND": {"weekdays": [5, 6]},
    "SUSPENSE_ACCOUNT": {"keywords": ["suspense", "clearing", "adjustment"]},
    "MANUAL_JOURNAL": {"keywords": ["manual", "adjustment", "correction"]},
    "UNUSUAL_POSTING": {"std_multiplier": 2, "min_count": 5},
}


def get_default_config(rule_code: str) -> dict[str, Any]:
    return dict(DEFAULT_RULE_CONFIGS.get(rule_code, {}))


def merge_rule_config(rule: RuleMaster, engagement_threshold: Decimal) -> dict[str, Any]:
    merged = get_default_config(rule.rule_code)
    if rule.config_schema:
        merged.update(rule.config_schema)

    if rule.rule_code == "LARGE_VALUE":
        threshold = merged.get("threshold")
        if threshold is None:
            merged["threshold"] = engagement_threshold
        else:
            merged["threshold"] = Decimal(str(threshold))

    return merged


def build_evaluation_context(
    rules_master: dict[str, RuleMaster],
    engagement_threshold: Decimal,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    configs: dict[str, dict[str, Any]] = {}
    for code, rule in rules_master.items():
        configs[code] = merge_rule_config(rule, engagement_threshold)
    return configs, set(rules_master.keys())
