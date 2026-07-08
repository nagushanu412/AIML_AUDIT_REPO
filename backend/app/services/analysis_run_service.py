from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditModuleCatalog, AuditProject, ModuleAnalysisRun
from app.repositories.module_catalog_repository import ModuleCatalogRepository
from app.services.project_access import get_owned_engagement, get_owned_project
from app.services.tenant_context import TenantContext

RUN_STATUSES = frozenset(
    {"draft", "running", "completed", "under_review", "approved", "locked", "archived"}
)

SUGGESTED_RUN_NAMES = [
    "Initial Submission",
    "Client Revision 1",
    "Client Revision 2",
    "Partner Review",
    "Final Audit",
    "Post Adjustment Review",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisRunService:
    def __init__(self, catalog_repo: ModuleCatalogRepository | None = None) -> None:
        self._catalog = catalog_repo or ModuleCatalogRepository()

    def list_runs(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        module_code: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ModuleAnalysisRun], int]:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = db.query(ModuleAnalysisRun).filter(
            ModuleAnalysisRun.engagement_id == engagement.id
        )
        if module_code:
            module = self._catalog.get_by_code(db, module_code.strip().upper())
            if module:
                query = query.filter(ModuleAnalysisRun.module_catalog_id == module.id)
        if status:
            query = query.filter(ModuleAnalysisRun.status == status.strip().lower())
        total = query.count()
        items = (
            query.order_by(ModuleAnalysisRun.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return items, total

    def create_run(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        module_code: str,
        run_name: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> ModuleAnalysisRun:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        module = self._catalog.get_by_code(db, module_code.strip().upper())
        if not module:
            raise ValueError(f"Module '{module_code}' not found.")

        if project_id:
            project = get_owned_project(db, project_id, tenant)
            if project.engagement_id != engagement.id:
                raise ValueError("Project does not belong to this engagement.")
        else:
            project = (
                db.query(AuditProject)
                .filter(
                    AuditProject.engagement_id == engagement.id,
                )
                .first()
            )

        name = (run_name or SUGGESTED_RUN_NAMES[0]).strip()
        run = ModuleAnalysisRun(
            engagement_id=engagement.id,
            project_id=project.id if project else None,
            module_catalog_id=module.id,
            organization_id=engagement.organization_id or tenant.organization_id,
            run_name=name,
            status="draft",
            run_owner_id=tenant.user.id,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def start_run(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        if run.status != "draft":
            raise ValueError("Only draft runs can be started.")
        self._assert_no_concurrent_running(db, run)

        run.status = "running"
        run.started_at = _now()
        run.job_id = str(uuid.uuid4())
        run.progress_pct = 0
        run.progress_message = "Analysis queued"
        db.commit()
        db.refresh(run)
        return run

    def complete_run(
        self,
        db: Session,
        tenant: TenantContext,
        run_id: uuid.UUID,
        *,
        success: bool = True,
        error_message: str | None = None,
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        if run.status != "running":
            raise ValueError("Run is not in running state.")

        if success:
            run.status = "completed"
            run.progress_pct = 100
            run.progress_message = "Analysis completed"
            run.completed_at = _now()
            run.error_message = None
        else:
            run.retry_count += 1
            if run.retry_count >= run.max_retries:
                run.status = "draft"
                run.error_message = error_message or "Analysis failed"
                run.progress_message = "Failed after max retries"
            else:
                run.status = "draft"
                run.error_message = error_message
                run.progress_message = f"Retry {run.retry_count}/{run.max_retries}"

        db.commit()
        db.refresh(run)
        return run

    def get_run(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        return self._get_run(db, tenant, run_id)

    def submit_for_review(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        self._assert_mutable(run)
        if run.status != "completed":
            raise ValueError("Only completed runs can be submitted for review.")
        run.status = "under_review"
        run.submitted_for_review_at = _now()
        db.commit()
        db.refresh(run)
        return run

    def approve_run(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        self._assert_mutable(run)
        if run.status != "under_review":
            raise ValueError("Only runs under review can be approved.")
        if tenant.member_role not in {"partner", "organization_owner", "audit_manager"}:
            raise PermissionError("Only partners or managers can approve analysis runs.")

        now = _now()
        run.status = "locked"
        run.approved_at = now
        run.locked_at = now
        db.commit()
        db.refresh(run)
        return run

    def return_to_auditor(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        self._assert_mutable(run)
        if run.status != "under_review":
            raise ValueError("Only runs under review can be returned to the auditor.")
        run.status = "completed"
        db.commit()
        db.refresh(run)
        return run

    def designate_official(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        if tenant.member_role not in {"partner", "organization_owner"}:
            raise PermissionError("Only partners can designate an official run.")
        if run.status not in {"approved", "locked"}:
            raise ValueError("Only approved or locked runs can be designated official.")
        if not run.module_catalog_id:
            raise ValueError("Run is not linked to a module.")

        prior = (
            db.query(ModuleAnalysisRun)
            .filter(
                ModuleAnalysisRun.engagement_id == run.engagement_id,
                ModuleAnalysisRun.module_catalog_id == run.module_catalog_id,
                ModuleAnalysisRun.is_official.is_(True),
                ModuleAnalysisRun.id != run.id,
            )
            .all()
        )
        for previous in prior:
            previous.is_official = False

        run.is_official = True
        db.commit()
        db.refresh(run)
        return run

    def archive_run(
        self, db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = self._get_run(db, tenant, run_id)
        if run.status not in {"locked", "approved"}:
            raise ValueError("Only locked or approved runs can be archived.")
        if tenant.member_role not in {
            "partner",
            "organization_owner",
            "audit_manager",
        }:
            raise PermissionError("You do not have permission to archive this run.")
        run.status = "archived"
        run.archived_at = _now()
        if run.is_official:
            run.is_official = False
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def assert_run_mutable(run: ModuleAnalysisRun) -> None:
        AnalysisRunService._assert_mutable(run)

    @staticmethod
    def _assert_mutable(run: ModuleAnalysisRun) -> None:
        if run.status in {"locked", "archived"}:
            raise ValueError(
                "This analysis run is locked or archived. Create a new run to continue."
            )

    @staticmethod
    def _get_run(
        db: Session, tenant: TenantContext, run_id: uuid.UUID
    ) -> ModuleAnalysisRun:
        run = db.query(ModuleAnalysisRun).filter(ModuleAnalysisRun.id == run_id).first()
        if not run:
            raise ValueError("Analysis run not found.")
        get_owned_engagement(db, run.engagement_id, tenant)
        return run

    @staticmethod
    def _assert_no_concurrent_running(db: Session, run: ModuleAnalysisRun) -> None:
        existing = (
            db.query(ModuleAnalysisRun)
            .filter(
                ModuleAnalysisRun.engagement_id == run.engagement_id,
                ModuleAnalysisRun.module_catalog_id == run.module_catalog_id,
                ModuleAnalysisRun.status == "running",
                ModuleAnalysisRun.id != run.id,
            )
            .first()
        )
        if existing:
            raise ValueError(
                "Another analysis run is already running for this module on this engagement."
            )

    @staticmethod
    def to_out(run: ModuleAnalysisRun, module: AuditModuleCatalog | None = None) -> dict:
        return {
            "id": run.id,
            "engagement_id": run.engagement_id,
            "project_id": run.project_id,
            "module_catalog_id": run.module_catalog_id,
            "module_code": module.code if module else None,
            "run_name": run.run_name,
            "status": run.status,
            "is_official": run.is_official,
            "job_id": run.job_id,
            "progress_pct": run.progress_pct,
            "progress_message": run.progress_message,
            "error_message": run.error_message,
            "retry_count": run.retry_count,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "created_at": run.created_at,
        }
