from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.review_workflow import (
    ApprovalCreate,
    ApprovalDecision,
    ApprovalOut,
    ReviewCommentCreate,
    ReviewCommentOut,
)
from app.services.audit_log_service import AuditLogService
from app.services.review_workflow_service import ReviewWorkflowService
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Review Workflow"])
_review = ReviewWorkflowService()
_audit_logs = AuditLogService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/findings/{finding_id}/comments", response_model=list[ReviewCommentOut])
def list_finding_comments(
    finding_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        comments = _review.list_comments(db, tenant, finding_id)
        return [ReviewCommentOut(**_review.comment_to_out(c)) for c in comments]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/findings/{finding_id}/comments",
    response_model=ReviewCommentOut,
    status_code=201,
)
def add_finding_comment(
    finding_id: UUID,
    body: ReviewCommentCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        comment = _review.add_comment(
            db,
            tenant,
            finding_id,
            body=body.body,
            comment_type=body.comment_type,
            parent_comment_id=body.parent_comment_id,
        )
        _audit_logs.write_log(
            db,
            action="review.comment",
            entity_type="review_comment",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=comment.id,
            details={"finding_id": str(finding_id)},
        )
        return ReviewCommentOut(**_review.comment_to_out(comment))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/findings/{finding_id}/approve",
    response_model=ApprovalOut,
    status_code=201,
)
def request_finding_approval(
    finding_id: UUID,
    body: ApprovalCreate | None = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        approval = _review.request_finding_approval(
            db,
            tenant,
            finding_id,
            comments=body.comments if body else None,
        )
        return ApprovalOut(**_review.approval_to_out(approval))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.get("/findings/{finding_id}/approvals", response_model=list[ApprovalOut])
def list_finding_approvals(
    finding_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        rows = _review.list_finding_approvals(db, tenant, finding_id)
        return [ApprovalOut(**_review.approval_to_out(a)) for a in rows]
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.patch("/approvals/{approval_id}", response_model=ApprovalOut)
def decide_approval(
    approval_id: UUID,
    body: ApprovalDecision,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        approval = _review.decide_approval(
            db,
            tenant,
            approval_id,
            status=body.status,
            comments=body.comments,
        )
        _audit_logs.write_log(
            db,
            action="approval.decide",
            entity_type="approval",
            user_id=tenant.user.id,
            organization_id=tenant.organization_id,
            entity_id=approval_id,
            details={"status": body.status},
        )
        return ApprovalOut(**_review.approval_to_out(approval))
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
