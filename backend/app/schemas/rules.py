from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RuleSummaryItem(BaseModel):
    rule_code: str = Field(..., example="LARGE_VALUE")
    rule_name: str = Field(..., example="Large Value Entries")
    description: str
    violation_count: int = Field(..., example=3)


class RunRulesResponse(BaseModel):
    project_id: UUID
    total_entries_analyzed: int = Field(..., example=21)
    total_violations_found: int = Field(..., example=15)
    violations_by_rule: dict[str, int] = Field(
        ...,
        example={"LARGE_VALUE": 3, "WEEKEND": 2, "YEAR_END": 4},
    )
    rule_summary: list[RuleSummaryItem]
    message: str


class RuleResultOut(BaseModel):
    id: UUID
    journal_entry_id: UUID
    rule_code: str
    rule_name: str
    triggered: bool
    details: str | None = None
    journal_id: str | None = None
    posting_date: date | None = None
    account_name: str | None = None
    amount: Decimal | None = None
    user_id: str | None = None
    created_at: datetime | None = None


class RuleResultsListResponse(BaseModel):
    project_id: UUID
    total_results: int
    results: list[RuleResultOut]
