from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditEngagement, AuditProject, Client, User


def get_owned_project(db: Session, project_id: uuid.UUID, user: User) -> AuditProject:
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
    if project.engagement.client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def get_owned_client(db: Session, client_id: uuid.UUID, user: User) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_owned_engagement(db: Session, engagement_id: uuid.UUID, user: User) -> AuditEngagement:
    engagement = (
        db.query(AuditEngagement)
        .join(Client)
        .filter(AuditEngagement.id == engagement_id, Client.user_id == user.id)
        .first()
    )
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return engagement
