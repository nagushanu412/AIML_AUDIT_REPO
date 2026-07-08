from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.subscription import (
    ChangePlanRequest,
    SubscriptionPlanOut,
    SubscriptionSummaryOut,
)
from app.services.audit_log_service import AuditLogService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
_subscription_service = SubscriptionService()
_audit_logs = AuditLogService()


def _handle_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/plans", response_model=list[SubscriptionPlanOut])
def list_subscription_plans(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    del current_user
    return _subscription_service.list_plans(db)


@router.get("/me", response_model=SubscriptionSummaryOut)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _subscription_service.get_subscription_summary(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/me", response_model=SubscriptionSummaryOut)
def change_my_subscription_plan(
    body: ChangePlanRequest,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        _subscription_service.change_plan(db, current_user, plan_code=body.plan_code)
        summary = _subscription_service.get_subscription_summary(db, current_user)
        _audit_logs.write_log(
            db,
            action="subscription.change_plan",
            entity_type="organization_subscription",
            user_id=current_user.id,
            organization_id=summary["subscription"]["organization_id"],
            entity_id=summary["subscription"]["id"],
            details={"plan_code": body.plan_code, "plan_name": summary["plan"]["name"]},
        )
        return summary
    except ValueError as exc:
        raise _handle_service_error(exc) from exc
