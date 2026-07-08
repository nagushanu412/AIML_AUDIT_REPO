"""Base class for module plugins."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditProject, Report
from app.schemas.upload import ValidationResult
from app.services.module_framework.protocol import (
    ModuleMetadata,
    RunRiskResult,
    RunRulesResult,
)


class BaseModuleProvider(ABC):
    code: str
    project_type: str

    def __init__(self, metadata: ModuleMetadata) -> None:
        self._metadata = metadata

    def get_metadata(self) -> ModuleMetadata:
        return self._metadata

    def ensure_project_type(self, project: AuditProject) -> None:
        if project.project_type != self.project_type:
            raise ValueError(
                f"Project type '{project.project_type}' does not match module "
                f"'{self.code}' (expected '{self.project_type}')."
            )

    @abstractmethod
    def validate_upload(self, content: bytes) -> tuple[ValidationResult, Any, dict]: ...

    @abstractmethod
    def save_upload(
        self, db: Session, project: AuditProject, payload: Any, extras: dict
    ) -> int: ...

    @abstractmethod
    def count_records(self, db: Session, project_id: uuid.UUID) -> int: ...

    @abstractmethod
    def run_rules(self, db: Session, project_id: uuid.UUID) -> RunRulesResult: ...

    @abstractmethod
    def run_risk(self, db: Session, project_id: uuid.UUID) -> RunRiskResult: ...

    @abstractmethod
    def generate_findings(self, db: Session, project_id: uuid.UUID) -> list: ...

    @abstractmethod
    def list_risk_scores(
        self,
        db: Session,
        project_id: uuid.UUID,
        *,
        risk_category: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]: ...

    @abstractmethod
    def list_findings(self, db: Session, project_id: uuid.UUID) -> list: ...

    @abstractmethod
    def default_report_type(self) -> str: ...

    @abstractmethod
    def generate_report(
        self,
        db: Session,
        project: AuditProject,
        user_id: uuid.UUID,
        report_type: str | None = None,
    ) -> Report: ...
