"""ModuleProvider protocol and shared types."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.models.audit import AuditProject, Report
from app.schemas.upload import ValidationResult


@dataclass
class ModuleMetadata:
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
    ui_config: dict = field(default_factory=dict)
    plugin_config: dict = field(default_factory=dict)


@dataclass
class UploadResult:
    project_id: uuid.UUID
    validation: ValidationResult
    records_imported: int
    message: str
    extras: dict = field(default_factory=dict)


@dataclass
class RunRulesResult:
    project_id: uuid.UUID
    total_rules_run: int
    total_violations: int
    rule_summary: dict[str, int]
    message: str = ""
    legacy_payload: dict = field(default_factory=dict)


@dataclass
class RunRiskResult:
    project_id: uuid.UUID
    total_scored: int
    high_risk: int
    medium_risk: int
    low_risk: int
    message: str = ""
    legacy_payload: dict = field(default_factory=dict)


@dataclass
class AnalysisPipelineResult:
    run_id: uuid.UUID
    project_id: uuid.UUID
    module_code: str
    steps_completed: list[str]
    findings_count: int
    report_id: uuid.UUID | None = None


@runtime_checkable
class ModuleProvider(Protocol):
    """Contract for audit module plugins."""

    code: str
    project_type: str

    def get_metadata(self) -> ModuleMetadata: ...

    def ensure_project_type(self, project: AuditProject) -> None: ...

    def validate_upload(self, content: bytes) -> tuple[ValidationResult, Any, dict]: ...

    def save_upload(
        self, db: Session, project: AuditProject, payload: Any, extras: dict
    ) -> int: ...

    def count_records(self, db: Session, project_id: uuid.UUID) -> int: ...

    def run_rules(self, db: Session, project_id: uuid.UUID) -> RunRulesResult: ...

    def run_risk(self, db: Session, project_id: uuid.UUID) -> RunRiskResult: ...

    def generate_findings(self, db: Session, project_id: uuid.UUID) -> list: ...

    def list_risk_scores(
        self,
        db: Session,
        project_id: uuid.UUID,
        *,
        risk_category: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]: ...

    def list_findings(self, db: Session, project_id: uuid.UUID) -> list: ...

    def default_report_type(self) -> str: ...

    def generate_report(
        self,
        db: Session,
        project: AuditProject,
        user_id: uuid.UUID,
        report_type: str | None = None,
    ) -> Report: ...
