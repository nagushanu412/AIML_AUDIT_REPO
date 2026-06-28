from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.services.procurement_constants import PROCUREMENT_RULE_DEFINITIONS


def _is_round_amount(amount: Decimal, suffixes: tuple[int, ...]) -> bool:
    value = int(abs(amount))
    if value % 1000 == 0:
        return True
    return any(value >= s and value % s == 0 for s in suffixes)


def _gst_rate_matches(taxable: Decimal, gst: Decimal, allowed_rates: list[int], tol: float) -> bool:
    if taxable <= 0:
        return gst == 0
    actual = float(gst / taxable * 100)
    return any(abs(actual - r) <= tol for r in allowed_rates)


def evaluate_procurement_rules(
    invoices: list[dict[str, Any]],
    *,
    high_value_threshold: Decimal,
    financial_year_end: date,
    rule_configs: dict[str, dict[str, Any]] | None = None,
    active_rule_codes: set[str] | None = None,
) -> list[dict[str, Any]]:
    configs = rule_configs or {}
    active = active_rule_codes or set(PROCUREMENT_RULE_DEFINITIONS.keys())
    violations: list[dict[str, Any]] = []

    po_cfg = configs.get("PROC_MISSING_PO", {"min_amount": 100000})
    gst_cfg = configs.get("PROC_GST_MISMATCH", {"allowed_rates": [0, 5, 12, 18, 28], "tolerance_pct": 1.0})
    round_cfg = configs.get("PROC_ROUND_AMOUNT", {"suffixes": [1000, 5000, 10000]})
    high_cfg = configs.get("PROC_HIGH_VALUE", {"threshold": float(high_value_threshold)})
    gstin_cfg = configs.get("PROC_MISSING_GSTIN", {"min_amount": 250000})
    cutoff_cfg = configs.get("PROC_CUTOFF", {"days_before": 7})

    threshold = Decimal(str(high_cfg.get("threshold", high_value_threshold)))
    po_min = Decimal(str(po_cfg.get("min_amount", 100000)))
    gstin_min = Decimal(str(gstin_cfg.get("min_amount", 250000)))
    days_before = int(cutoff_cfg.get("days_before", 7))
    ye_start = financial_year_end - timedelta(days=days_before - 1)
    ye_end = financial_year_end
    round_suffixes = tuple(int(s) for s in round_cfg.get("suffixes", [1000, 5000, 10000]))
    allowed_rates = [int(r) for r in gst_cfg.get("allowed_rates", [0, 5, 12, 18, 28])]
    tolerance = float(gst_cfg.get("tolerance_pct", 1.0))

    seen: dict[tuple[str, str], list[UUID]] = {}
    for inv in invoices:
        key = (str(inv.get("invoice_no", "")).lower(), str(inv.get("vendor_name", "")).lower())
        seen.setdefault(key, []).append(inv["id"])
    duplicate_ids = {iid for ids in seen.values() if len(ids) > 1 for iid in ids}

    for inv in invoices:
        inv_id: UUID = inv["id"]
        inv_date: date = inv["invoice_date"]
        taxable: Decimal = inv["taxable_amount"]
        gst: Decimal = inv["gst_amount"]
        total: Decimal = inv["total_amount"]
        gstin = (inv.get("vendor_gstin") or "").strip()
        po = (inv.get("po_number") or "").strip()

        checks = [
            (
                "PROC_DUPLICATE_PAYMENT",
                "PROC_DUPLICATE_PAYMENT" in active,
                inv_id in duplicate_ids,
                f"Duplicate invoice {inv.get('invoice_no')} for vendor {inv.get('vendor_name')}.",
            ),
            (
                "PROC_MISSING_PO",
                "PROC_MISSING_PO" in active,
                total >= po_min and not po,
                f"Invoice {total:,.2f} has no PO reference (threshold {po_min:,.2f}).",
            ),
            (
                "PROC_GST_MISMATCH",
                "PROC_GST_MISMATCH" in active,
                taxable > 0 and not _gst_rate_matches(taxable, gst, allowed_rates, tolerance),
                f"GST {gst:,.2f} on taxable {taxable:,.2f} does not match standard rates.",
            ),
            (
                "PROC_HIGH_VALUE",
                "PROC_HIGH_VALUE" in active,
                total > threshold,
                f"Invoice total {total:,.2f} exceeds threshold {threshold:,.2f}.",
            ),
            (
                "PROC_ROUND_AMOUNT",
                "PROC_ROUND_AMOUNT" in active,
                _is_round_amount(total, round_suffixes),
                f"Invoice total {total:,.2f} is a round figure.",
            ),
            (
                "PROC_MISSING_GSTIN",
                "PROC_MISSING_GSTIN" in active,
                total >= gstin_min and not gstin,
                f"Invoice {total:,.2f} has no vendor GSTIN.",
            ),
            (
                "PROC_CUTOFF",
                "PROC_CUTOFF" in active,
                ye_start <= inv_date <= ye_end,
                f"Invoice dated {inv_date} within year-end window {ye_start} to {ye_end}.",
            ),
        ]

        for rule_code, is_active, triggered, details in checks:
            if is_active and triggered:
                violations.append(
                    {
                        "procurement_invoice_id": inv_id,
                        "invoice_no": inv.get("invoice_no"),
                        "rule_code": rule_code,
                        "rule_name": PROCUREMENT_RULE_DEFINITIONS[rule_code]["name"],
                        "triggered": True,
                        "details": details,
                    }
                )

    return violations
