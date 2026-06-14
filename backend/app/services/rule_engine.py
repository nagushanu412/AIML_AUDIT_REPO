from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import numpy as np

from app.services.constants import RULE_DEFINITIONS
from app.services.rule_config import DEFAULT_RULE_CONFIGS, get_default_config


def _is_round_amount(amount: Decimal, suffixes: tuple[int, ...]) -> bool:
    value = int(abs(amount))
    if value % 1000 == 0:
        return True
    for suffix in suffixes:
        if value >= suffix and value % suffix == 0:
            return True
    return False


def _year_end_window(financial_year_end: date, days_before: int) -> tuple[date, date]:
    return financial_year_end - timedelta(days=days_before - 1), financial_year_end


def _compute_unusual_users(
    user_counts: Counter[str],
    *,
    std_multiplier: float,
    min_count: float,
) -> set[str]:
    if not user_counts:
        return set()
    counts = np.array(list(user_counts.values()), dtype=float)
    mean = counts.mean()
    std = counts.std() if len(counts) > 1 else 0.0
    threshold = max(mean + std_multiplier * std, mean * 2, min_count)
    return {user_id for user_id, count in user_counts.items() if count > threshold}


def _resolve_configs(
    rule_configs: dict[str, dict[str, Any]] | None,
    large_value_threshold: Decimal,
) -> dict[str, dict[str, Any]]:
    if rule_configs is not None:
        return rule_configs

    configs: dict[str, dict[str, Any]] = {}
    for code in RULE_DEFINITIONS:
        merged = get_default_config(code)
        if code == "LARGE_VALUE":
            merged["threshold"] = large_value_threshold
        configs[code] = merged
    return configs


def evaluate_rules(
    entries: list[dict[str, Any]],
    *,
    large_value_threshold: Decimal,
    financial_year_end: date,
    rule_configs: dict[str, dict[str, Any]] | None = None,
    active_rule_codes: set[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Evaluate audit rules against journal entries.

    Each entry dict must include: id, journal_id, posting_date, account_name,
    amount, user_id, description.
    Returns only triggered violations for active rules.
    """
    configs = _resolve_configs(rule_configs, large_value_threshold)
    active = active_rule_codes or set(RULE_DEFINITIONS.keys())

    large_cfg = configs.get("LARGE_VALUE", DEFAULT_RULE_CONFIGS["LARGE_VALUE"])
    year_cfg = configs.get("YEAR_END", DEFAULT_RULE_CONFIGS["YEAR_END"])
    round_cfg = configs.get("ROUND_AMOUNT", DEFAULT_RULE_CONFIGS["ROUND_AMOUNT"])
    weekend_cfg = configs.get("WEEKEND", DEFAULT_RULE_CONFIGS["WEEKEND"])
    suspense_cfg = configs.get("SUSPENSE_ACCOUNT", DEFAULT_RULE_CONFIGS["SUSPENSE_ACCOUNT"])
    manual_cfg = configs.get("MANUAL_JOURNAL", DEFAULT_RULE_CONFIGS["MANUAL_JOURNAL"])
    unusual_cfg = configs.get("UNUSUAL_POSTING", DEFAULT_RULE_CONFIGS["UNUSUAL_POSTING"])

    threshold = Decimal(str(large_cfg.get("threshold", large_value_threshold)))
    days_before = int(year_cfg.get("days_before", 7))
    round_suffixes = tuple(int(s) for s in round_cfg.get("suffixes", [500, 1000, 5000]))
    weekend_days = set(int(d) for d in weekend_cfg.get("weekdays", [5, 6]))
    suspense_keywords = tuple(str(k).lower() for k in suspense_cfg.get("keywords", []))
    manual_keywords = tuple(str(k).lower() for k in manual_cfg.get("keywords", []))
    std_multiplier = float(unusual_cfg.get("std_multiplier", 2))
    min_count = float(unusual_cfg.get("min_count", 5))

    user_counts: Counter[str] = Counter(e["user_id"] for e in entries)
    unusual_users = _compute_unusual_users(
        user_counts,
        std_multiplier=std_multiplier,
        min_count=min_count,
    )
    ye_start, ye_end = _year_end_window(financial_year_end, days_before)
    violations: list[dict[str, Any]] = []

    for entry in entries:
        entry_id: UUID = entry["id"]
        amount: Decimal = entry["amount"]
        posting: date = entry["posting_date"]
        account_name = (entry.get("account_name") or "").lower()
        description = (entry.get("description") or "").lower()
        user_id = entry["user_id"]

        checks = [
            (
                "LARGE_VALUE",
                "LARGE_VALUE" in active,
                amount > threshold,
                f"Amount {amount:,.2f} exceeds threshold {threshold:,.2f}.",
            ),
            (
                "YEAR_END",
                "YEAR_END" in active,
                ye_start <= posting <= ye_end,
                f"Posted on {posting} within year-end window {ye_start} to {ye_end}.",
            ),
            (
                "ROUND_AMOUNT",
                "ROUND_AMOUNT" in active,
                _is_round_amount(amount, round_suffixes),
                f"Amount {amount:,.2f} is a round figure.",
            ),
            (
                "WEEKEND",
                "WEEKEND" in active,
                posting.weekday() in weekend_days,
                f"Posted on {posting.strftime('%A')} (non-business day).",
            ),
            (
                "SUSPENSE_ACCOUNT",
                "SUSPENSE_ACCOUNT" in active,
                any(kw in account_name for kw in suspense_keywords),
                f"Account '{entry.get('account_name')}' matches suspense/clearing/adjustment pattern.",
            ),
            (
                "MANUAL_JOURNAL",
                "MANUAL_JOURNAL" in active,
                any(kw in description for kw in manual_keywords),
                "Description indicates manual adjustment or correction.",
            ),
            (
                "UNUSUAL_POSTING",
                "UNUSUAL_POSTING" in active,
                user_id in unusual_users,
                f"User {user_id} posted {user_counts[user_id]} entries (above normal pattern).",
            ),
        ]

        for rule_code, is_active, triggered, details in checks:
            if is_active and triggered:
                violations.append(
                    {
                        "journal_entry_id": entry_id,
                        "journal_id": entry.get("journal_id"),
                        "rule_code": rule_code,
                        "rule_name": RULE_DEFINITIONS[rule_code]["name"],
                        "triggered": True,
                        "details": details,
                    }
                )

    return violations
