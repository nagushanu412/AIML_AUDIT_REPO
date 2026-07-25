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


def _engagement_accessible(engagement: AuditEngagement, tenant: TenantContext) -> bool:
    """Tenant boundary is engagement.organization_id only (no client.organization_id fallback)."""
    if tenant.organization_id:
        return engagement.organization_id == tenant.organization_id
    client = engagement.client
    return client is not None and client.user_id == tenant.user.id


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
    if not _engagement_accessible(project.engagement, tenant):
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
    if not _engagement_accessible(engagement, tenant):
        raise HTTPException(status_code=403, detail="Access denied")
    return engagement


def ensure_engagement_organization_id(
    db: Session,
    engagement: AuditEngagement,
    tenant: TenantContext,
    *,
    persist: bool = True,
) -> uuid.UUID:
    """Return engagement.organization_id. No client/tenant fallback after Remediation M1 Step 1."""
    del db, persist  # retained for call-site compatibility; no longer used for backfill
    if not engagement.organization_id:
        raise ValueError(
            "This engagement is not linked to an organization. "
            "organization_id is required on audit_engagements."
        )
    if tenant.organization_id and engagement.organization_id != tenant.organization_id:
        raise ValueError("Engagement organization does not match the current tenant.")
    return engagement.organization_id


def client_list_filter(tenant: TenantContext):
    """SQLAlchemy filter for listing clients visible to the tenant."""
    if tenant.organization_id:
        return Client.organization_id == tenant.organization_id
    return Client.user_id == tenant.user.id


def engagement_list_query(db: Session, tenant: TenantContext):
    query = db.query(AuditEngagement).join(Client)
    if tenant.organization_id:
        return query.filter(AuditEngagement.organization_id == tenant.organization_id)
    return query.filter(Client.user_id == tenant.user.id)


def project_list_query(db: Session, tenant: TenantContext):
    query = db.query(AuditProject).join(AuditEngagement).join(Client)
    if tenant.organization_id:
        return query.filter(AuditEngagement.organization_id == tenant.organization_id)
    return query.filter(Client.user_id == tenant.user.id)
