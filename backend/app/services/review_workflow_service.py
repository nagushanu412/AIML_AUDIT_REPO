from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.audit import Approval, AuditFinding, AuditProject, ReviewComment
from app.services.finding_lifecycle_service import FindingLifecycleService
from app.services.project_access import get_owned_engagement
from app.services.tenant_context import TenantContext

REVIEWER_ROLES = frozenset(
    {"organization_owner", "partner", "audit_manager", "senior_auditor", "reviewer"}
)
PARTNER_APPROVE_ROLES = frozenset({"organization_owner", "partner"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewWorkflowService:
    def __init__(self) -> None:
        self._findings = FindingLifecycleService()

    def add_comment(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        body: str,
        comment_type: str = "review",
        parent_comment_id: uuid.UUID | None = None,
    ) -> ReviewComment:
        if (tenant.member_role or "") not in REVIEWER_ROLES:
            raise PermissionError("You do not have permission to add review comments.")
        finding = self._findings._get_owned_finding(db, tenant, finding_id)
        project = db.query(AuditProject).filter(AuditProject.id == finding.project_id).first()
        if not body.strip():
            raise ValueError("Comment body is required.")
        normalized_type = comment_type.strip().lower()
        if normalized_type not in {"review", "clarification", "partner_note"}:
            raise ValueError("Invalid comment type.")

        comment = ReviewComment(
            engagement_id=project.engagement_id if project else finding.project_id,
            finding_id=finding.id,
            project_id=finding.project_id,
            parent_comment_id=parent_comment_id,
            comment_type=normalized_type,
            body=body.strip(),
            created_by=tenant.user.id,
        )
        if project:
            comment.engagement_id = project.engagement_id
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return self._load_comment(db, comment.id)

    def list_comments(
        self, db: Session, tenant: TenantContext, finding_id: uuid.UUID
    ) -> list[ReviewComment]:
        self._findings._get_owned_finding(db, tenant, finding_id)
        return (
            db.query(ReviewComment)
            .options(joinedload(ReviewComment.author))
            .filter(ReviewComment.finding_id == finding_id)
            .order_by(ReviewComment.created_at.asc())
            .all()
        )

    def request_finding_approval(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        comments: str | None = None,
    ) -> Approval:
        finding = self._findings._get_owned_finding(db, tenant, finding_id)
        project = db.query(AuditProject).filter(AuditProject.id == finding.project_id).first()
        approval = Approval(
            engagement_id=project.engagement_id,
            finding_id=finding.id,
            project_id=finding.project_id,
            approval_type="finding",
            status="pending",
            comments=comments,
            created_by=tenant.user.id,
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return self._load_approval(db, approval.id)

    def decide_approval(
        self,
        db: Session,
        tenant: TenantContext,
        approval_id: uuid.UUID,
        *,
        status: str,
        comments: str | None = None,
    ) -> Approval:
        if (tenant.member_role or "") not in PARTNER_APPROVE_ROLES:
            raise PermissionError("Only a partner can approve or reject.")
        normalized = status.strip().lower()
        if normalized not in {"approved", "rejected"}:
            raise ValueError("Status must be approved or rejected.")

        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise ValueError("Approval not found.")
        get_owned_engagement(db, approval.engagement_id, tenant)

        approval.status = normalized
        approval.comments = comments or approval.comments
        approval.approver_id = tenant.user.id
        approval.approved_at = _now()

        # Approval-row updates are partner-workflow specific; finding status must
        # go through FindingLifecycleService.update_status (history + reviewed_*).
        finding_status_committed = False
        if normalized == "approved" and approval.finding_id:
            finding = db.query(AuditFinding).filter(AuditFinding.id == approval.finding_id).first()
            if finding and finding.status in {"under_review", "open"}:
                self._findings.update_status(
                    db,
                    tenant,
                    finding.id,
                    status="accepted",
                    change_reason=comments or "Partner approval",
                )
                finding_status_committed = True

        if not finding_status_committed:
            db.commit()
        return self._load_approval(db, approval.id)

    def list_finding_approvals(
        self, db: Session, tenant: TenantContext, finding_id: uuid.UUID
    ) -> list[Approval]:
        self._findings._get_owned_finding(db, tenant, finding_id)
        return (
            db.query(Approval)
            .options(joinedload(Approval.approver))
            .filter(Approval.finding_id == finding_id)
            .order_by(Approval.created_at.desc())
            .all()
        )

    @staticmethod
    def _load_comment(db: Session, comment_id: uuid.UUID) -> ReviewComment:
        return (
            db.query(ReviewComment)
            .options(joinedload(ReviewComment.author))
            .filter(ReviewComment.id == comment_id)
            .first()
        )

    @staticmethod
    def _load_approval(db: Session, approval_id: uuid.UUID) -> Approval:
        return (
            db.query(Approval)
            .options(joinedload(Approval.approver))
            .filter(Approval.id == approval_id)
            .first()
        )

    @staticmethod
    def comment_to_out(c: ReviewComment) -> dict:
        author = c.author
        return {
            "id": c.id,
            "engagement_id": c.engagement_id,
            "finding_id": c.finding_id,
            "parent_comment_id": c.parent_comment_id,
            "comment_type": c.comment_type,
            "body": c.body,
            "status": c.status,
            "created_by": c.created_by,
            "author_name": author.full_name if author else None,
            "created_at": c.created_at,
        }

    @staticmethod
    def approval_to_out(a: Approval) -> dict:
        approver = a.approver
        return {
            "id": a.id,
            "engagement_id": a.engagement_id,
            "finding_id": a.finding_id,
            "approval_type": a.approval_type,
            "status": a.status,
            "comments": a.comments,
            "approver_id": a.approver_id,
            "approver_name": approver.full_name if approver else None,
            "approved_at": a.approved_at,
            "created_at": a.created_at,
        }
