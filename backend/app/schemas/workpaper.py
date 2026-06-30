from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkpaperCreate(BaseModel):
    reference_code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="testing", max_length=50)
    description: str | None = Field(None, max_length=5000)
    status: str = Field(default="draft", max_length=50)
    project_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class WorkpaperUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    category: str | None = Field(None, max_length=50)
    status: str | None = Field(None, max_length=50)
    metadata: dict[str, Any] | None = None


class WorkpaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    project_id: UUID | None
    analysis_run_id: UUID | None
    root_workpaper_id: UUID | None
    version_number: int
    is_current: bool
    reference_code: str
    title: str
    description: str | None
    category: str
    file_name: str | None
    content_type: str | None
    file_size_bytes: int | None
    file_hash: str | None
    has_file: bool
    status: str
    metadata: dict[str, Any]
    created_by: UUID | None
    created_by_name: str | None
    created_at: datetime
    updated_at: datetime


class WorkpaperListOut(BaseModel):
    items: list[WorkpaperOut]
    total: int
    limit: int
    offset: int
