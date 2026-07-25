from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FindingLifecycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    project_type: str | None = None
    project_name: str | None = None
    module_code: str | None = None
    module_name: str | None = None
    rule_code: str
    finding_title: str
    observation: str
    risk_level: str
    impact: str
    recommendation: str
    affected_count: int
    rule_content_version: int | None = None
    status: str
    management_response: str | None
    remediation_status: str
    remediation_notes: str | None
    remediation_due_date: date | None
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class FindingListOut(BaseModel):
    items: list[FindingLifecycleOut]
    total: int
    limit: int
    offset: int


class FindingStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)
    change_reason: str | None = Field(None, max_length=2000)


class ManagementResponseUpdate(BaseModel):
    response: str = Field(..., min_length=1, max_length=10000)
    change_reason: str | None = Field(None, max_length=2000)


class RemediationUpdate(BaseModel):
    remediation_status: str | None = Field(None, max_length=50)
    remediation_notes: str | None = Field(None, max_length=5000)
    remediation_due_date: date | None = None
    change_reason: str | None = Field(None, max_length=2000)


class FindingHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finding_id: UUID
    previous_status: str | None
    new_status: str
    action: str
    change_reason: str | None
    management_response_snapshot: str | None
    changed_by: UUID | None
    changed_by_name: str | None
    created_at: datetime


class FindingRelationshipCreate(BaseModel):
    target_finding_id: UUID
    relationship_type: str = Field(default="related", max_length=50)
    notes: str | None = Field(None, max_length=2000)


class FindingRelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    source_finding_id: UUID
    target_finding_id: UUID
    relationship_type: str
    notes: str | None
    created_by: UUID | None
    created_at: datetime
