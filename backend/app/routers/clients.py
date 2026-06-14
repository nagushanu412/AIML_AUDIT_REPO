from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import Client, User
from app.schemas.hierarchy import ClientCreate, ClientOut, ClientUpdate
from app.services.project_access import get_owned_client

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    return (
        db.query(Client)
        .filter(
            Client.user_id == current_user.id,
            Client.name.notin_(("Default Client", "Migrated Client")),
        )
        .order_by(Client.name)
        .all()
    )


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    client = Client(user_id=current_user.id, **body.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    return get_owned_client(db, client_id, current_user)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: UUID,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    client = get_owned_client(db, client_id, current_user)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    client = get_owned_client(db, client_id, current_user)
    db.delete(client)
    db.commit()
