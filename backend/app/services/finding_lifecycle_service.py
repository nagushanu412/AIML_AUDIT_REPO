from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditFinding, AuditProject, FindingStatusHistory
from app.services.finding_lifecycle_constants import (
    FINDING_APPROVE_ROLES,
    FINDING_REOPEN_ROLES,
    FINDING_STATUSES,
    FINDING_UPDATE_ROLES,
    PRE_DECISION_STATUSES,
    REMEDIATION_STATUSES,
    STATUS_TRANSITIONS,
)
from app.services.module_catalog_constants import (
    PROJECT_TYPE_TO_MODULE_CODE,
    PROJECT_TYPE_TO_MODULE_NAME,
)
from app.services.project_access import get_owned_engagement, get_owned_project
from app.services.run_lock_guard import assert_project_allows_mutation
from app.services.tenant_context import TenantContext


@dataclass(frozen=True)
class FindingListResult:
    items: list[AuditFinding]
    total: int


class FindingLifecycleService:
    def list_engagement_findings(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        status: str | None = None,
        risk_level: str | None = None,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> FindingListResult:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = (
            db.query(AuditFinding)
            .join(AuditProject)
            .filter(AuditProject.engagement_id == engagement.id)
        )
        if status:
            self._validate_status(status)
            query = query.filter(AuditFinding.status == status.strip().lower())
        if risk_level:
            query = query.filter(AuditFinding.risk_level == risk_level.strip().lower())
        if project_id:
            project = get_owned_project(db, project_id, tenant)
            if project.engagement_id != engagement.id:
                raise ValueError("Project does not belong to this engagement.")
            query = query.filter(AuditFinding.project_id == project_id)

        total = query.count()
        items = (
            query.options(joinedload(AuditFinding.project))
            .order_by(AuditFinding.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return FindingListResult(items=items, total=total)

    def get_finding(
        self, db: Session, tenant: TenantContext, finding_id: uuid.UUID
    ) -> AuditFinding:
        finding = self._get_owned_finding(db, tenant, finding_id)
        return finding

    def update_status(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        status: str,
        change_reason: str | None = None,
    ) -> AuditFinding:
        self._assert_can_update(tenant)
        finding = self._get_owned_finding(db, tenant, finding_id)
        assert_project_allows_mutation(db, finding.project_id)
        new_status = self._validate_status(status)
        current = finding.status or "open"

        if new_status == current:
            raise ValueError(f"Finding is already in status '{current}'.")

        allowed = STATUS_TRANSITIONS.get(current, frozenset())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{current}' to '{new_status}'."
            )

        if new_status in {"cleared", "accepted", "closed"}:
            self._assert_can_approve(tenant)
        if current == "closed" and new_status == "open":
            self._assert_can_reopen(tenant)

        action = "reopened" if current == "closed" and new_status == "open" else "status_change"
        self._write_history(
            db,
            finding=finding,
            previous_status=current,
            new_status=new_status,
            action=action,
            changed_by=tenant.user.id,
            change_reason=change_reason,
        )

        finding.status = new_status
        finding.updated_by = tenant.user.id
        if new_status in PRE_DECISION_STATUSES:
            finding.reviewed_by = None
            finding.reviewed_at = None
        else:
            finding.reviewed_by = tenant.user.id
            finding.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return self._load(db, finding.id)

    def set_management_response(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        response: str,
        change_reason: str | None = None,
    ) -> AuditFinding:
        self._assert_can_update(tenant)
        finding = self._get_owned_finding(db, tenant, finding_id)
        assert_project_allows_mutation(db, finding.project_id)
        if not response.strip():
            raise ValueError("Management response cannot be empty.")

        finding.management_response = response.strip()
        finding.updated_by = tenant.user.id

        self._write_history(
            db,
            finding=finding,
            previous_status=finding.status,
            new_status=finding.status,
            action="management_response",
            changed_by=tenant.user.id,
            change_reason=change_reason,
            management_response_snapshot=finding.management_response,
        )

        db.commit()
        return self._load(db, finding.id)

    def update_remediation(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        remediation_status: str | None = None,
        remediation_notes: str | None = None,
        remediation_due_date: date | None = None,
        change_reason: str | None = None,
    ) -> AuditFinding:
        self._assert_can_update(tenant)
        finding = self._get_owned_finding(db, tenant, finding_id)
        assert_project_allows_mutation(db, finding.project_id)

        if remediation_status is not None:
            finding.remediation_status = self._validate_remediation_status(
                remediation_status
            )
        if remediation_notes is not None:
            finding.remediation_notes = remediation_notes
        if remediation_due_date is not None:
            finding.remediation_due_date = remediation_due_date

        finding.updated_by = tenant.user.id
        self._write_history(
            db,
            finding=finding,
            previous_status=finding.status,
            new_status=finding.status,
            action="remediation_update",
            changed_by=tenant.user.id,
            change_reason=change_reason,
        )

        db.commit()
        return self._load(db, finding.id)

    def list_history(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FindingStatusHistory]:
        finding = self._get_owned_finding(db, tenant, finding_id)
        return (
            db.query(FindingStatusHistory)
            .options(joinedload(FindingStatusHistory.changer))
            .filter(FindingStatusHistory.finding_id == finding.id)
            .order_by(FindingStatusHistory.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )

    @staticmethod
    def _get_owned_finding(
        db: Session, tenant: TenantContext, finding_id: uuid.UUID
    ) -> AuditFinding:
        finding = (
            db.query(AuditFinding)
            .options(joinedload(AuditFinding.project))
            .join(AuditProject)
            .join(AuditProject.engagement)
            .filter(AuditFinding.id == finding_id)
            .first()
        )
        if not finding:
            raise ValueError("Finding not found.")
        get_owned_project(db, finding.project_id, tenant)
        return finding

    @staticmethod
    def _load(db: Session, finding_id: uuid.UUID) -> AuditFinding:
        finding = db.query(AuditFinding).filter(AuditFinding.id == finding_id).first()
        if not finding:
            raise ValueError("Finding not found.")
        return finding

    @staticmethod
    def _assert_can_update(tenant: TenantContext) -> None:
        if (tenant.member_role or "") not in FINDING_UPDATE_ROLES:
            raise PermissionError("You do not have permission to update findings.")

    @staticmethod
    def _assert_can_approve(tenant: TenantContext) -> None:
        if (tenant.member_role or "") not in FINDING_APPROVE_ROLES:
            raise PermissionError(
                "You do not have permission to clear, accept, or close findings."
            )

    @staticmethod
    def _assert_can_reopen(tenant: TenantContext) -> None:
        if (tenant.member_role or "") not in FINDING_REOPEN_ROLES:
            raise PermissionError("You do not have permission to reopen findings.")

    @staticmethod
    def _validate_status(status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in FINDING_STATUSES:
            allowed = ", ".join(sorted(FINDING_STATUSES))
            raise ValueError(f"Invalid status. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_remediation_status(status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in REMEDIATION_STATUSES:
            allowed = ", ".join(sorted(REMEDIATION_STATUSES))
            raise ValueError(f"Invalid remediation status. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _write_history(
        db: Session,
        *,
        finding: AuditFinding,
        previous_status: str | None,
        new_status: str,
        action: str,
        changed_by: uuid.UUID,
        change_reason: str | None,
        management_response_snapshot: str | None = None,
    ) -> None:
        db.add(
            FindingStatusHistory(
                finding_id=finding.id,
                previous_status=previous_status,
                new_status=new_status,
                action=action,
                change_reason=change_reason,
                management_response_snapshot=management_response_snapshot,
                changed_by=changed_by,
            )
        )

    @staticmethod
    def module_context_for_finding(finding: AuditFinding) -> dict[str, str | None]:
        project = finding.project
        project_type = project.project_type if project else None
        module_name, module_code = FindingLifecycleService._resolve_module_labels(
            project_type, finding.rule_code
        )
        return {
            "project_type": project_type,
            "project_name": project.name if project else None,
            "module_code": module_code,
            "module_name": module_name,
        }

    @staticmethod
    def _resolve_module_labels(
        project_type: str | None, rule_code: str
    ) -> tuple[str, str]:
        if project_type and project_type in PROJECT_TYPE_TO_MODULE_NAME:
            return (
                PROJECT_TYPE_TO_MODULE_NAME[project_type],
                PROJECT_TYPE_TO_MODULE_CODE[project_type],
            )
        if rule_code.startswith("REV_"):
            return "Revenue Testing", "REVENUE_TESTING"
        if rule_code.startswith("PROC_"):
            return "Procurement Testing", "PROCUREMENT_TESTING"
        return "Journal Entry Testing", "JOURNAL_ENTRY_TESTING"

    @staticmethod
    def to_out(finding: AuditFinding) -> dict:
        return {
            "id": finding.id,
            "project_id": finding.project_id,
            **FindingLifecycleService.module_context_for_finding(finding),
            "rule_code": finding.rule_code,
            "finding_title": finding.finding_title,
            "observation": finding.observation,
            "risk_level": finding.risk_level,
            "impact": finding.impact,
            "recommendation": finding.recommendation,
            "affected_count": finding.affected_count,
            "rule_content_version": finding.rule_content_version,
            "status": finding.status or "open",
            "management_response": finding.management_response,
            "remediation_status": finding.remediation_status or "not_started",
            "remediation_notes": finding.remediation_notes,
            "remediation_due_date": finding.remediation_due_date,
            "reviewed_by": finding.reviewed_by,
            "reviewed_at": finding.reviewed_at,
            "updated_by": finding.updated_by,
            "created_at": finding.created_at,
            "updated_at": finding.updated_at,
        }

    @staticmethod
    def history_to_out(entry: FindingStatusHistory) -> dict:
        changer = entry.changer
        return {
            "id": entry.id,
            "finding_id": entry.finding_id,
            "previous_status": entry.previous_status,
            "new_status": entry.new_status,
            "action": entry.action,
            "change_reason": entry.change_reason,
            "management_response_snapshot": entry.management_response_snapshot,
            "changed_by": entry.changed_by,
            "changed_by_name": changer.full_name if changer else None,
            "created_at": entry.created_at,
        }
