from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    gstin: str | None = None
    pan: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    status: str = "active"


class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    gstin: str | None = None
    pan: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    status: str | None = None


class ClientOut(BaseModel):
    id: UUID
    name: str
    industry: str | None
    gstin: str | None
    pan: str | None
    contact_person: str | None
    contact_email: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EngagementCreate(BaseModel):
    client_id: UUID
    financial_year: str = Field(min_length=1, max_length=20)
    audit_type: str = "Statutory"
    status: str = "planned"
    start_date: date | None = None
    end_date: date | None = None
    financial_year_end: date
    large_value_threshold: Decimal = Decimal("100000.00")


class EngagementUpdate(BaseModel):
    financial_year: str | None = None
    audit_type: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    financial_year_end: date | None = None
    large_value_threshold: Decimal | None = None


class EngagementOut(BaseModel):
    id: UUID
    client_id: UUID
    financial_year: str
    audit_type: str
    status: str
    start_date: date | None
    end_date: date | None
    financial_year_end: date
    large_value_threshold: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    engagement_id: UUID
    name: str = Field(min_length=1, max_length=255)
    project_type: str = "journal_testing"
    status: str = "active"


class ProjectUpdate(BaseModel):
    name: str | None = None
    project_type: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: UUID
    engagement_id: UUID
    name: str
    project_type: str
    status: str
    total_entries: int
    created_at: datetime

    model_config = {"from_attributes": True}
