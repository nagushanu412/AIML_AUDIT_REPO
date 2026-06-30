from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import (
    AuditEngagement,
    AuditFinding,
    AuditProject,
    EngagementEnabledModule,
    ModuleAnalysisRun,
    ReportHistory,
)
from app.services.analysis_run_service import AnalysisRunService
from app.services.engagement_module_service import EngagementModuleService
from app.services.engagement_team_service import EngagementTeamService
from app.services.project_access import get_owned_engagement
from app.services.tenant_context import TenantContext


class EngagementHubService:
    def __init__(self) -> None:
        self._modules = EngagementModuleService()
        self._team = EngagementTeamService()
        self._runs = AnalysisRunService()

    def get_hub_summary(
        self, db: Session, tenant: TenantContext, engagement_id: uuid.UUID
    ) -> dict:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        modules = self._modules.list_enabled_modules(db, tenant, engagement_id)
        team = self._team.get_team_summary(db, tenant, engagement_id)
        runs, _ = self._runs.list_runs(db, tenant, engagement_id, limit=10)

        official_runs = (
            db.query(ModuleAnalysisRun)
            .filter(
                ModuleAnalysisRun.engagement_id == engagement.id,
                ModuleAnalysisRun.is_official.is_(True),
            )
            .all()
        )
        latest_runs = (
            db.query(ModuleAnalysisRun)
            .filter(ModuleAnalysisRun.engagement_id == engagement.id)
            .order_by(ModuleAnalysisRun.created_at.desc())
            .limit(5)
            .all()
        )

        findings_count = (
            db.query(AuditFinding)
            .join(AuditProject)
            .filter(AuditProject.engagement_id == engagement.id)
            .count()
        )

        return {
            "engagement_id": engagement.id,
            "financial_year": engagement.financial_year,
            "status": engagement.status,
            "enabled_modules": modules,
            "team_summary": team,
            "official_runs": [AnalysisRunService.to_out(r) for r in official_runs],
            "latest_runs": [AnalysisRunService.to_out(r) for r in latest_runs],
            "findings_count": findings_count,
            "pending_actions": self._pending_actions(db, engagement),
        }

    @staticmethod
    def _pending_actions(db: Session, engagement: AuditEngagement) -> list[str]:
        actions: list[str] = []
        if not (
            db.query(EngagementEnabledModule)
            .filter(
                EngagementEnabledModule.engagement_id == engagement.id,
                EngagementEnabledModule.is_enabled.is_(True),
            )
            .first()
        ):
            actions.append("Enable audit modules")
        running = (
            db.query(ModuleAnalysisRun)
            .filter(
                ModuleAnalysisRun.engagement_id == engagement.id,
                ModuleAnalysisRun.status == "running",
            )
            .count()
        )
        if running:
            actions.append(f"{running} analysis run(s) in progress")
        return actions


class EngagementReportService:
    def generate_consolidated_report(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
    ) -> ReportHistory:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        projects = (
            db.query(AuditProject)
            .filter(AuditProject.engagement_id == engagement.id)
            .all()
        )

        summary = {
            "engagement_id": str(engagement.id),
            "financial_year": engagement.financial_year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "modules": [],
            "findings_total": 0,
        }

        for project in projects:
            findings = (
                db.query(AuditFinding)
                .filter(AuditFinding.project_id == project.id)
                .all()
            )
            summary["modules"].append(
                {
                    "project_id": str(project.id),
                    "project_type": project.project_type,
                    "findings_count": len(findings),
                    "high_risk": sum(1 for f in findings if f.risk_level == "high"),
                }
            )
            summary["findings_total"] += len(findings)

        content = json.dumps(summary, indent=2).encode("utf-8")
        history_id = uuid.uuid4()
        file_name = f"engagement_report_{engagement.financial_year.replace(' ', '_')}.json"
        storage_key, file_hash = save_report_artifact(
            engagement.id, history_id, file_name, content
        )

        max_version = (
            db.query(ReportHistory)
            .filter(
                ReportHistory.engagement_id == engagement.id,
                ReportHistory.report_type == "engagement_consolidated",
            )
            .count()
        )

        row = ReportHistory(
            id=history_id,
            engagement_id=engagement.id,
            report_type="engagement_consolidated",
            version_number=max_version + 1,
            file_name=file_name,
            storage_key=storage_key,
            generated_by=tenant.user.id,
            metadata_={"file_hash": file_hash, **summary},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def to_out(row: ReportHistory) -> dict:
        return {
            "id": row.id,
            "engagement_id": row.engagement_id,
            "report_type": row.report_type,
            "version_number": row.version_number,
            "is_official": row.is_official,
            "file_name": row.file_name,
            "created_at": row.created_at,
            "metadata": row.metadata_ or {},
        }
