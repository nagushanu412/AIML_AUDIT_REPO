from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import AuditEngagement, Client, User
from app.schemas.hierarchy import EngagementCreate, EngagementOut, EngagementUpdate
from app.services.project_access import get_owned_client, get_owned_engagement

router = APIRouter(prefix="/engagements", tags=["Engagements"])


@router.get("", response_model=list[EngagementOut])
def list_engagements(
    client_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    query = (
        db.query(AuditEngagement)
        .join(Client)
        .filter(Client.user_id == current_user.id)
    )
    if client_id:
        get_owned_client(db, client_id, current_user)
        query = query.filter(AuditEngagement.client_id == client_id)
    return query.order_by(AuditEngagement.financial_year.desc()).all()


@router.post("", response_model=EngagementOut, status_code=201)
def create_engagement(
    body: EngagementCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    get_owned_client(db, body.client_id, current_user)
    engagement = AuditEngagement(**body.model_dump())
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return engagement


@router.get("/{engagement_id}", response_model=EngagementOut)
def get_engagement(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    return get_owned_engagement(db, engagement_id, current_user)


@router.patch("/{engagement_id}", response_model=EngagementOut)
def update_engagement(
    engagement_id: UUID,
    body: EngagementUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    engagement = get_owned_engagement(db, engagement_id, current_user)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(engagement, key, value)
    db.commit()
    db.refresh(engagement)
    return engagement


@router.delete("/{engagement_id}", status_code=204)
def delete_engagement(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    engagement = get_owned_engagement(db, engagement_id, current_user)
    db.delete(engagement)
    db.commit()
