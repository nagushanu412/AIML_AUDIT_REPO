from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.services.revenue_constants import REVENUE_RULE_DEFINITIONS


def _is_round_amount(amount: Decimal, suffixes: tuple[int, ...]) -> bool:
    value = int(abs(amount))
    if value % 1000 == 0:
        return True
    for suffix in suffixes:
        if value >= suffix and value % suffix == 0:
            return True
    return False


def _gst_rate_matches(taxable: Decimal, gst: Decimal, allowed_rates: list[int], tolerance_pct: float) -> bool:
    if taxable <= 0:
        return gst == 0
    actual_rate = float(gst / taxable * 100)
    for rate in allowed_rates:
        if abs(actual_rate - rate) <= tolerance_pct:
            return True
    return False


def _cutoff_window(financial_year_end: date, days_before: int) -> tuple[date, date]:
    return financial_year_end - timedelta(days=days_before - 1), financial_year_end


def evaluate_revenue_rules(
    invoices: list[dict[str, Any]],
    *,
    high_value_threshold: Decimal,
    financial_year_end: date,
    rule_configs: dict[str, dict[str, Any]] | None = None,
    active_rule_codes: set[str] | None = None,
) -> list[dict[str, Any]]:
    configs = rule_configs or {}
    active = active_rule_codes or set(REVENUE_RULE_DEFINITIONS.keys())
    violations: list[dict[str, Any]] = []

    dup_cfg = configs.get("REV_DUPLICATE_INVOICE", {})
    cutoff_cfg = configs.get("REV_CUTOFF", {"days_before": 7})
    gst_cfg = configs.get("REV_GST_MISMATCH", {"allowed_rates": [0, 5, 12, 18, 28], "tolerance_pct": 1.0})
    round_cfg = configs.get("REV_ROUND_AMOUNT", {"suffixes": [1000, 5000, 10000, 50000, 100000]})
    high_cfg = configs.get("REV_HIGH_VALUE", {"threshold": float(high_value_threshold)})
    gstin_cfg = configs.get("REV_MISSING_GSTIN", {"min_amount": 250000})
    unpaid_cfg = configs.get("REV_UNPAID_LARGE", {"min_amount": 500000, "statuses": ["unpaid", "partial"]})

    threshold = Decimal(str(high_cfg.get("threshold", high_value_threshold)))
    days_before = int(cutoff_cfg.get("days_before", 7))
    ye_start, ye_end = _cutoff_window(financial_year_end, days_before)
    round_suffixes = tuple(int(s) for s in round_cfg.get("suffixes", [1000, 5000, 10000]))
    allowed_rates = [int(r) for r in gst_cfg.get("allowed_rates", [0, 5, 12, 18, 28])]
    tolerance = float(gst_cfg.get("tolerance_pct", 1.0))
    gstin_min = Decimal(str(gstin_cfg.get("min_amount", 250000)))
    unpaid_min = Decimal(str(unpaid_cfg.get("min_amount", 500000)))
    unpaid_statuses = {str(s).lower() for s in unpaid_cfg.get("statuses", ["unpaid", "partial"])}

    seen_keys: dict[tuple[str, str], list[UUID]] = {}
    for inv in invoices:
        key = (str(inv.get("invoice_no", "")).lower(), str(inv.get("customer_name", "")).lower())
        seen_keys.setdefault(key, []).append(inv["id"])

    duplicate_ids = {iid for ids in seen_keys.values() if len(ids) > 1 for iid in ids}

    for inv in invoices:
        inv_id: UUID = inv["id"]
        inv_date: date = inv["invoice_date"]
        taxable: Decimal = inv["taxable_amount"]
        gst: Decimal = inv["gst_amount"]
        total: Decimal = inv["total_amount"]
        gstin = (inv.get("customer_gstin") or "").strip()
        payment = (inv.get("payment_status") or "").strip().lower()

        checks = [
            (
                "REV_DUPLICATE_INVOICE",
                "REV_DUPLICATE_INVOICE" in active,
                inv_id in duplicate_ids,
                f"Duplicate invoice {inv.get('invoice_no')} for customer {inv.get('customer_name')}.",
            ),
            (
                "REV_CUTOFF",
                "REV_CUTOFF" in active,
                ye_start <= inv_date <= ye_end,
                f"Invoice dated {inv_date} within year-end window {ye_start} to {ye_end}.",
            ),
            (
                "REV_GST_MISMATCH",
                "REV_GST_MISMATCH" in active,
                taxable > 0 and not _gst_rate_matches(taxable, gst, allowed_rates, tolerance),
                f"GST {gst:,.2f} on taxable {taxable:,.2f} does not match standard rates.",
            ),
            (
                "REV_ROUND_AMOUNT",
                "REV_ROUND_AMOUNT" in active,
                _is_round_amount(total, round_suffixes),
                f"Invoice total {total:,.2f} is a round figure.",
            ),
            (
                "REV_HIGH_VALUE",
                "REV_HIGH_VALUE" in active,
                total > threshold,
                f"Invoice total {total:,.2f} exceeds threshold {threshold:,.2f}.",
            ),
            (
                "REV_MISSING_GSTIN",
                "REV_MISSING_GSTIN" in active,
                total >= gstin_min and not gstin,
                f"Invoice {total:,.2f} has no customer GSTIN (B2B threshold {gstin_min:,.2f}).",
            ),
            (
                "REV_UNPAID_LARGE",
                "REV_UNPAID_LARGE" in active,
                total >= unpaid_min and payment in unpaid_statuses,
                f"Large invoice {total:,.2f} marked as {payment or 'unpaid'}.",
            ),
        ]

        for rule_code, is_active, triggered, details in checks:
            if is_active and triggered:
                violations.append(
                    {
                        "revenue_invoice_id": inv_id,
                        "invoice_no": inv.get("invoice_no"),
                        "rule_code": rule_code,
                        "rule_name": REVENUE_RULE_DEFINITIONS[rule_code]["name"],
                        "triggered": True,
                        "details": details,
                    }
                )

    return violations
