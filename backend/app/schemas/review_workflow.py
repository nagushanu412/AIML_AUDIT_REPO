from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)
    comment_type: str = Field(default="review", max_length=50)
    parent_comment_id: UUID | None = None


class ReviewCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    finding_id: UUID | None
    parent_comment_id: UUID | None
    comment_type: str
    body: str
    status: str
    created_by: UUID | None
    author_name: str | None
    created_at: datetime


class ApprovalCreate(BaseModel):
    comments: str | None = Field(None, max_length=5000)


class ApprovalDecision(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    comments: str | None = Field(None, max_length=5000)


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    finding_id: UUID | None
    approval_type: str
    status: str
    comments: str | None
    approver_id: UUID | None
    approver_name: str | None
    approved_at: datetime | None
    created_at: datetime
