from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EngagementTeamAssign(BaseModel):
    user_id: UUID
    role: str = Field(..., min_length=1, max_length=50)
    notes: str | None = Field(None, max_length=2000)
    change_reason: str | None = Field(None, max_length=2000)


class EngagementTeamUpdate(BaseModel):
    role: str | None = Field(None, min_length=1, max_length=50)
    notes: str | None = Field(None, max_length=2000)
    change_reason: str | None = Field(None, max_length=2000)


class EngagementTeamRemove(BaseModel):
    change_reason: str | None = Field(None, max_length=2000)


class EngagementTeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    status: str
    is_primary: bool
    notes: str | None
    assigned_by: UUID | None
    assigned_by_name: str | None
    assigned_at: datetime
    removed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EngagementTeamListOut(BaseModel):
    items: list[EngagementTeamMemberOut]
    total: int
    limit: int
    offset: int


class EngagementTeamHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    team_member_id: UUID | None
    user_id: UUID
    user_email: str
    user_full_name: str
    role: str
    action: str
    previous_role: str | None
    changed_by: UUID | None
    changed_by_name: str | None
    change_reason: str | None
    created_at: datetime


class EngagementTeamHistoryListOut(BaseModel):
    items: list[EngagementTeamHistoryOut]
    total: int
    limit: int
    offset: int


class EngagementTeamSummaryOut(BaseModel):
    engagement_id: UUID
    total_active: int
    partner: EngagementTeamMemberOut | None
    audit_manager: EngagementTeamMemberOut | None
    by_role: dict[str, list[EngagementTeamMemberOut]]
