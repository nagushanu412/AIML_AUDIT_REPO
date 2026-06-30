from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EngagementModuleOut(BaseModel):
    id: UUID
    engagement_id: UUID
    module_code: str
    module_name: str
    module_slug: str
    category: str
    implementation_status: str
    is_enabled: bool
    enabled_at: datetime
