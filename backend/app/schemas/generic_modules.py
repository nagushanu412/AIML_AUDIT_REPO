"""Generic module API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.analytics import FindingOut, ReportOut
from app.schemas.upload import ValidationResult


class ModuleMetadataOut(BaseModel):
    code: str
    name: str
    project_type: str
    slug: str
    category: str
    icon: str
    implementation_status: str
    input_format: str = "xlsx"
    rule_prefix: str = ""
    theme_color: str = "blue"
    ui_config: dict = Field(default_factory=dict)
    plugin_config: dict = Field(default_factory=dict)


class GenericUploadResponse(BaseModel):
    project_id: UUID
    module_code: str
    validation: ValidationResult
    records_imported: int
    message: str
    extras: dict = Field(default_factory=dict)


class GenericRunRulesResponse(BaseModel):
    project_id: UUID
    module_code: str
    total_rules_run: int
    total_violations: int
    rule_summary: dict[str, int]
    message: str = ""


class GenericRunRiskResponse(BaseModel):
    project_id: UUID
    module_code: str
    total_scored: int
    high_risk: int
    medium_risk: int
    low_risk: int
    message: str = ""


class GenericRiskScoreOut(BaseModel):
    id: UUID | None = None
    project_id: UUID | None = None
    risk_category: str | None = None
    risk_score: float | None = None
    entity_id: UUID | None = None
    entity_label: str | None = None
    details: dict = Field(default_factory=dict)


class GenericFindingsResponse(BaseModel):
    project_id: UUID
    module_code: str
    total: int
    items: list[FindingOut]


class GenericReportsResponse(BaseModel):
    project_id: UUID
    module_code: str
    items: list[ReportOut]


class GenericReportGenerateResponse(BaseModel):
    module_code: str
    report: ReportOut


class ApiErrorDetail(BaseModel):
    detail: str
    code: str | None = None
    field: str | None = None


class ModuleWorkspaceConfigOut(BaseModel):
    module_code: str
    metadata: ModuleMetadataOut
    pipeline_steps: list[str]
    supported_endpoints: list[str]
    created_at: datetime | None = None
