from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import Client
from app.schemas.hierarchy import ClientCreate, ClientOut, ClientUpdate
from app.services.audit_log_service import AuditLogService
from app.services.subscription_enforcement import SubscriptionEnforcementService
from app.services.project_access import client_list_filter, get_owned_client
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/clients", tags=["Clients"])
_enforcement = SubscriptionEnforcementService()
_audit_logs = AuditLogService()


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    return (
        db.query(Client)
        .filter(
            client_list_filter(tenant),
            Client.name.notin_(("Default Client", "Migrated Client")),
        )
        .order_by(Client.name)
        .all()
    )


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        _enforcement.assert_can_add_client(db, tenant)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    client = Client(
        user_id=tenant.user.id,
        organization_id=tenant.organization_id,
        **body.model_dump(),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    _audit_logs.write_log(
        db,
        action="create",
        entity_type="client",
        user_id=tenant.user.id,
        organization_id=tenant.organization_id,
        entity_id=client.id,
        details={"name": client.name},
    )
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    return get_owned_client(db, client_id, tenant)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: UUID,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    client = get_owned_client(db, client_id, tenant)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    client = get_owned_client(db, client_id, tenant)
    db.delete(client)
    db.commit()
