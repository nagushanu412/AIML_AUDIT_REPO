from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    engagement_id: UUID
    project_id: UUID | None
    analysis_run_id: UUID | None
    root_evidence_id: UUID | None
    version_number: int
    is_current: bool
    title: str
    description: str | None
    category: str
    file_name: str
    content_type: str | None
    file_size_bytes: int
    file_hash: str | None
    status: str
    metadata: dict[str, Any]
    uploaded_by: UUID | None
    uploaded_by_name: str | None
    created_at: datetime
    updated_at: datetime


class EvidenceListOut(BaseModel):
    items: list[EvidenceOut]
    total: int
    limit: int
    offset: int


class EvidenceLinkCreate(BaseModel):
    linked_entity_type: str = Field(..., min_length=1, max_length=50)
    linked_entity_id: UUID
    link_type: str = Field(default="reference", max_length=50)
    finding_id: UUID | None = None
    workpaper_id: UUID | None = None
    notes: str | None = Field(None, max_length=2000)


class EvidenceLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evidence_id: UUID
    engagement_id: UUID
    finding_id: UUID | None
    workpaper_id: UUID | None
    linked_entity_type: str
    linked_entity_id: UUID
    link_type: str
    notes: str | None
    created_by: UUID | None
    created_at: datetime
