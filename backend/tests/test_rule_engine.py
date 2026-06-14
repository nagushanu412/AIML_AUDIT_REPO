"""Unit tests for the journal entry rule engine — one test per rule."""

from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.rule_engine import evaluate_rules

FIXTURES = Path(__file__).parent / "fixtures" / "rule_test_entries.json"
FY_END = date(2025, 3, 31)
THRESHOLD = Decimal("100000")


def _load_fixture() -> list[dict]:
    with FIXTURES.open(encoding="utf-8") as f:
        raw = json.load(f)
    for item in raw:
        item["id"] = uuid.UUID(item["id"])
        item["posting_date"] = date.fromisoformat(item["posting_date"])
        item["amount"] = Decimal(item["amount"])
    return raw


def _run(entries: list[dict]) -> list[dict]:
    return evaluate_rules(
        entries,
        large_value_threshold=THRESHOLD,
        financial_year_end=FY_END,
    )


def _codes_for_journal(violations: list[dict], journal_id: str) -> set[str]:
    return {
        v["rule_code"]
        for v in violations
        if v.get("journal_id") == journal_id
    }


class TestLargeValueRule:
    def test_flags_amount_above_threshold(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-1",
                "posting_date": date(2025, 1, 15),
                "account_name": "Cash",
                "amount": Decimal("150000"),
                "user_id": "U1",
                "description": "Payment",
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "LARGE_VALUE" for v in violations)

    def test_passes_amount_below_threshold(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-2",
                "posting_date": date(2025, 1, 15),
                "account_name": "Cash",
                "amount": Decimal("50000"),
                "user_id": "U1",
                "description": "Payment",
            }
        ]
        violations = _run(entries)
        assert not any(v["rule_code"] == "LARGE_VALUE" for v in violations)


class TestYearEndRule:
    def test_flags_last_seven_days_of_fy(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-YE",
                "posting_date": date(2025, 3, 28),
                "account_name": "Revenue",
                "amount": Decimal("10000"),
                "user_id": "U1",
                "description": "Accrual",
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "YEAR_END" for v in violations)

    def test_passes_mid_year_date(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-MID",
                "posting_date": date(2025, 6, 15),
                "account_name": "Revenue",
                "amount": Decimal("10000"),
                "user_id": "U1",
                "description": "Sale",
            }
        ]
        violations = _run(entries)
        assert not any(v["rule_code"] == "YEAR_END" for v in violations)


class TestRoundAmountRule:
    @pytest.mark.parametrize(
        "amount",
        [Decimal("5000"), Decimal("10000"), Decimal("50000"), Decimal("100000")],
    )
    def test_flags_round_amounts(self, amount: Decimal):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-R",
                "posting_date": date(2025, 1, 10),
                "account_name": "Expense",
                "amount": amount,
                "user_id": "U1",
                "description": "Bill",
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "ROUND_AMOUNT" for v in violations)

    def test_passes_non_round_amount(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-NR",
                "posting_date": date(2025, 1, 10),
                "account_name": "Expense",
                "amount": Decimal("1234.56"),
                "user_id": "U1",
                "description": "Bill",
            }
        ]
        violations = _run(entries)
        assert not any(v["rule_code"] == "ROUND_AMOUNT" for v in violations)


class TestWeekendRule:
    def test_flags_saturday(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-SAT",
                "posting_date": date(2025, 2, 8),
                "account_name": "Misc",
                "amount": Decimal("5000"),
                "user_id": "U1",
                "description": "Post",
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "WEEKEND" for v in violations)

    def test_passes_weekday(self):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-WD",
                "posting_date": date(2025, 2, 10),
                "account_name": "Misc",
                "amount": Decimal("5000"),
                "user_id": "U1",
                "description": "Post",
            }
        ]
        violations = _run(entries)
        assert not any(v["rule_code"] == "WEEKEND" for v in violations)


class TestSuspenseAccountRule:
    @pytest.mark.parametrize("account_name", ["Suspense Account", "Bank Clearing", "Adjustment Ledger"])
    def test_flags_suspense_accounts(self, account_name: str):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-SUS",
                "posting_date": date(2025, 1, 10),
                "account_name": account_name,
                "amount": Decimal("8000"),
                "user_id": "U1",
                "description": "Entry",
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "SUSPENSE_ACCOUNT" for v in violations)


class TestManualJournalRule:
    @pytest.mark.parametrize("description", ["Manual entry", "Period adjustment", "Error correction"])
    def test_flags_manual_descriptions(self, description: str):
        entries = [
            {
                "id": uuid.uuid4(),
                "journal_id": "JV-MAN",
                "posting_date": date(2025, 1, 10),
                "account_name": "GL",
                "amount": Decimal("8000"),
                "user_id": "U1",
                "description": description,
            }
        ]
        violations = _run(entries)
        assert any(v["rule_code"] == "MANUAL_JOURNAL" for v in violations)


class TestUnusualPostingRule:
    def test_flags_high_volume_user(self):
        entries = []
        for i in range(10):
            entries.append(
                {
                    "id": uuid.uuid4(),
                    "journal_id": f"JV-U{i}",
                    "posting_date": date(2025, 1, 10),
                    "account_name": "Bank",
                    "amount": Decimal("1000"),
                    "user_id": "HEAVY_USER",
                    "description": "Transfer",
                }
            )
        for i in range(9):
            entries.append(
                {
                    "id": uuid.uuid4(),
                    "journal_id": f"JV-L{i}",
                    "posting_date": date(2025, 1, 11),
                    "account_name": "Bank",
                    "amount": Decimal("1000"),
                    "user_id": f"LIGHT_USER_{i}",
                    "description": "Transfer",
                }
            )
        violations = _run(entries)
        unusual = [v for v in violations if v["rule_code"] == "UNUSUAL_POSTING"]
        assert len(unusual) >= 1
        assert all("HEAVY_USER" in v["details"] for v in unusual)


class TestFixtureData:
    """Validate JSON fixture expected_rules against engine output."""

    def test_fixture_expected_rules(self):
        fixture = _load_fixture()
        violations = _run(fixture)
        for item in fixture:
            expected = set(item.pop("expected_rules"))
            actual = _codes_for_journal(violations, item["journal_id"])
            assert actual == expected, (
                f"{item['journal_id']}: expected {expected}, got {actual}"
            )
