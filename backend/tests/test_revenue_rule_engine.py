from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.revenue_rule_engine import evaluate_revenue_rules


def test_duplicate_invoice_rule():
    inv_id = uuid4()
    inv_id2 = uuid4()
    invoices = [
        {
            "id": inv_id,
            "invoice_no": "INV-001",
            "invoice_date": date(2026, 3, 15),
            "customer_name": "Acme",
            "customer_gstin": "29AABCA1234A1Z5",
            "taxable_amount": Decimal("100000"),
            "gst_amount": Decimal("18000"),
            "total_amount": Decimal("118000"),
            "payment_status": "Paid",
        },
        {
            "id": inv_id2,
            "invoice_no": "INV-001",
            "invoice_date": date(2026, 3, 15),
            "customer_name": "Acme",
            "customer_gstin": "29AABCA1234A1Z5",
            "taxable_amount": Decimal("100000"),
            "gst_amount": Decimal("18000"),
            "total_amount": Decimal("118000"),
            "payment_status": "Paid",
        },
    ]
    violations = evaluate_revenue_rules(
        invoices,
        high_value_threshold=Decimal("100000"),
        financial_year_end=date(2026, 3, 31),
    )
    codes = {v["rule_code"] for v in violations}
    assert "REV_DUPLICATE_INVOICE" in codes


def test_gst_mismatch_rule():
    inv_id = uuid4()
    invoices = [
        {
            "id": inv_id,
            "invoice_no": "INV-002",
            "invoice_date": date(2026, 3, 10),
            "customer_name": "Beta",
            "customer_gstin": "29AABCB5678B1Z5",
            "taxable_amount": Decimal("100000"),
            "gst_amount": Decimal("7000"),
            "total_amount": Decimal("107000"),
            "payment_status": "Paid",
        }
    ]
    violations = evaluate_revenue_rules(
        invoices,
        high_value_threshold=Decimal("100000"),
        financial_year_end=date(2026, 3, 31),
    )
    assert any(v["rule_code"] == "REV_GST_MISMATCH" for v in violations)
