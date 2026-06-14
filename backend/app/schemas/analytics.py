from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RiskScoreOut(BaseModel):
    id: UUID
    journal_entry_id: UUID
    total_score: int
    risk_category: str
    rule_breakdown: dict
    journal_id: str | None = None
    posting_date: date | None = None
    account_name: str | None = None
    amount: Decimal | None = None
    user_id: str | None = None


class RunRiskResponse(BaseModel):
    project_id: UUID
    total_entries_scored: int
    high_risk: int
    medium_risk: int
    low_risk: int
    message: str


class FindingOut(BaseModel):
    id: UUID
    rule_code: str
    finding_title: str
    observation: str
    risk_level: str
    impact: str
    recommendation: str
    affected_count: int
    created_at: datetime


class ReportOut(BaseModel):
    id: UUID
    project_id: UUID
    report_type: str
    file_name: str
    status: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class DashboardSummary(BaseModel):
    total_clients: int
    total_engagements: int
    total_projects: int
    total_journal_entries: int
    total_violations: int
    high_risk_entries: int
    medium_risk_entries: int = 0
    low_risk_entries: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    violations_by_rule: dict[str, int] = Field(default_factory=dict)
    recent_activities: list[dict] = Field(default_factory=list)
