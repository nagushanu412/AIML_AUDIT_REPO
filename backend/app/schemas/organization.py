from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.organization_constants import ORGANIZATION_STATUSES


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    settings: dict[str, Any] | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = None
    settings: dict[str, Any] | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ORGANIZATION_STATUSES:
            allowed = ", ".join(sorted(ORGANIZATION_STATUSES))
            raise ValueError(f"status must be one of: {allowed}")
        return value


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
