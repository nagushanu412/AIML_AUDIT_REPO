from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditEngagement, AuditProject, Client, User
from app.services.tenant_context import TenantContext


def _client_accessible(client: Client, tenant: TenantContext) -> bool:
    if tenant.organization_id:
        return client.organization_id == tenant.organization_id
    return client.user_id == tenant.user.id


def get_owned_project(
    db: Session, project_id: uuid.UUID, tenant: TenantContext
) -> AuditProject:
    project = (
        db.query(AuditProject)
        .options(
            joinedload(AuditProject.engagement).joinedload(AuditEngagement.client)
        )
        .filter(AuditProject.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _client_accessible(project.engagement.client, tenant):
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def get_owned_client(db: Session, client_id: uuid.UUID, tenant: TenantContext) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if not _client_accessible(client, tenant):
        raise HTTPException(status_code=403, detail="Access denied")
    return client


def get_owned_engagement(
    db: Session, engagement_id: uuid.UUID, tenant: TenantContext
) -> AuditEngagement:
    engagement = (
        db.query(AuditEngagement)
        .options(joinedload(AuditEngagement.client))
        .filter(AuditEngagement.id == engagement_id)
        .first()
    )
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    if not _client_accessible(engagement.client, tenant):
        raise HTTPException(status_code=403, detail="Access denied")
    return engagement


def ensure_engagement_organization_id(
    db: Session,
    engagement: AuditEngagement,
    tenant: TenantContext,
    *,
    persist: bool = True,
) -> uuid.UUID:
    """Resolve organization for legacy engagements missing organization_id."""
    if engagement.organization_id:
        return engagement.organization_id

    org_id: uuid.UUID | None = None
    client = engagement.client
    if client and client.organization_id:
        org_id = client.organization_id
    elif tenant.organization_id:
        org_id = tenant.organization_id

    if not org_id:
        raise ValueError(
            "This engagement is not linked to an organization. "
            "Team assignment requires an organization context."
        )

    if persist:
        engagement.organization_id = org_id
        if client and not client.organization_id:
            client.organization_id = org_id
        db.flush()

    return org_id


def client_list_filter(tenant: TenantContext):
    """SQLAlchemy filter for listing clients visible to the tenant."""
    if tenant.organization_id:
        return Client.organization_id == tenant.organization_id
    return Client.user_id == tenant.user.id


def engagement_list_query(db: Session, tenant: TenantContext):
    query = db.query(AuditEngagement).join(Client).filter(client_list_filter(tenant))
    return query


def project_list_query(db: Session, tenant: TenantContext):
    query = (
        db.query(AuditProject)
        .join(AuditEngagement)
        .join(Client)
        .filter(client_list_filter(tenant))
    )
    return query
