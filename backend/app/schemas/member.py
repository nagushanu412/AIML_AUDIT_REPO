from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.member_constants import INVITABLE_ROLES, MEMBER_ROLES, MEMBER_STATUSES


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="auditor")
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in INVITABLE_ROLES:
            allowed = ", ".join(sorted(INVITABLE_ROLES))
            raise ValueError(f"role must be one of: {allowed}")
        return normalized


class MemberUpdate(BaseModel):
    role: str | None = None
    status: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in MEMBER_ROLES:
            allowed = ", ".join(sorted(MEMBER_ROLES))
            raise ValueError(f"role must be one of: {allowed}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in MEMBER_STATUSES:
            allowed = ", ".join(sorted(MEMBER_STATUSES))
            raise ValueError(f"status must be one of: {allowed}")
        return normalized


class MemberOut(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    status: str
    invited_at: datetime | None
    joined_at: datetime
    created_at: datetime
    updated_at: datetime
    invite_email_sent: bool = False
    invite_link: str | None = None

    model_config = {"from_attributes": True}
