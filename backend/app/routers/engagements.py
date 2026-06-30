from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditEngagement
from app.schemas.hierarchy import EngagementCreate, EngagementOut, EngagementUpdate
from app.services.audit_log_service import AuditLogService
from app.services.subscription_enforcement import SubscriptionEnforcementService
from app.services.project_access import engagement_list_query, get_owned_client, get_owned_engagement
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Engagements"])
_enforcement = SubscriptionEnforcementService()
_audit_logs = AuditLogService()


@router.get("", response_model=list[EngagementOut])
def list_engagements(
    client_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    query = engagement_list_query(db, tenant)
    if client_id:
        get_owned_client(db, client_id, tenant)
        query = query.filter(AuditEngagement.client_id == client_id)
    return query.order_by(AuditEngagement.financial_year.desc()).all()


@router.post("", response_model=EngagementOut, status_code=201)
def create_engagement(
    body: EngagementCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    client = get_owned_client(db, body.client_id, tenant)
    try:
        _enforcement.assert_can_add_engagement(db, tenant)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    engagement = AuditEngagement(
        organization_id=client.organization_id or tenant.organization_id,
        **body.model_dump(),
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    _audit_logs.write_log(
        db,
        action="create",
        entity_type="engagement",
        user_id=tenant.user.id,
        organization_id=tenant.organization_id,
        entity_id=engagement.id,
        details={"financial_year": engagement.financial_year},
    )
    return engagement


@router.get("/{engagement_id}", response_model=EngagementOut)
def get_engagement(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    return get_owned_engagement(db, engagement_id, tenant)


@router.patch("/{engagement_id}", response_model=EngagementOut)
def update_engagement(
    engagement_id: UUID,
    body: EngagementUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    engagement = get_owned_engagement(db, engagement_id, tenant)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(engagement, key, value)
    db.commit()
    db.refresh(engagement)
    return engagement


@router.delete("/{engagement_id}", status_code=204)
def delete_engagement(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    engagement = get_owned_engagement(db, engagement_id, tenant)
    db.delete(engagement)
    db.commit()
