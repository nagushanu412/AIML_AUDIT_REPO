from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ModuleCatalogOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    category: str
    slug: str
    icon: str
    implementation_status: str
    display_order: int
    is_active: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
