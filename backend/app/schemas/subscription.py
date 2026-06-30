from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionPlanOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    max_users: int
    max_clients: int
    max_engagements: int
    max_storage_bytes: int
    monthly_ai_credits: int
    monthly_uploads: int
    max_reports: int
    enabled_module_codes: list[str]
    api_rate_limit: int
    support_level: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UsageLimitsOut(BaseModel):
    max_users: int
    max_clients: int
    max_engagements: int
    max_reports: int
    monthly_uploads: int
    max_storage_bytes: int
    monthly_ai_credits: int
    api_rate_limit: int


class UsageSnapshotOut(BaseModel):
    users: int
    clients: int
    engagements: int
    reports: int
    uploads: int
    storage_bytes: int
    ai_credits: int


class OrganizationSubscriptionOut(BaseModel):
    id: UUID
    organization_id: UUID
    status: str
    started_at: datetime
    ends_at: datetime | None = None


class SubscriptionSummaryOut(BaseModel):
    subscription: OrganizationSubscriptionOut
    plan: SubscriptionPlanOut
    usage: UsageSnapshotOut
    limits: UsageLimitsOut


class ChangePlanRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=50)
