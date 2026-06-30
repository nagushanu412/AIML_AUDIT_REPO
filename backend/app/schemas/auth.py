from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=10)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class InvitePreviewResponse(BaseModel):
    email: str
    full_name: str
    organization_name: str
    role: str
    role_label: str
    requires_password: bool


class AcceptInviteResponse(BaseModel):
    message: str
    requires_login: bool = False
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    user_id: UUID | None = None
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    organization_id: UUID | None = None
    member_role: str | None = None


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    email: str
    full_name: str
    role: str
    organization_id: UUID | None = None
    member_role: str | None = None


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    company_name: str | None = None
    phone: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}
