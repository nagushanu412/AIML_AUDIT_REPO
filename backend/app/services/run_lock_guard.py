"""Guards mutations against locked or archived analysis runs (Phase 2)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import ModuleAnalysisRun
from app.services.analysis_run_service import AnalysisRunService

_LOCKED_STATUSES = frozenset({"locked", "archived"})


def assert_run_allows_mutation(db: Session, run_id: uuid.UUID | None) -> None:
    if not run_id:
        return
    run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
    if run:
        AnalysisRunService.assert_run_mutable(run)


def assert_project_allows_mutation(db: Session, project_id: uuid.UUID | None) -> None:
    if not project_id:
        return
    locked = (
        db.query(ModuleAnalysisRun)
        .filter(
            ModuleAnalysisRun.project_id == project_id,
            ModuleAnalysisRun.status.in_(_LOCKED_STATUSES),
        )
        .first()
    )
    if locked:
        raise ValueError(
            "This workspace is linked to a locked or archived analysis run. "
            "Create a new run to continue."
        )
