from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])
_org_service = OrganizationService()


def _handle_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    body: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _org_service.create_organization(
            db,
            current_user,
            name=body.name,
            slug=body.slug,
            settings=body.settings,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.get("/me", response_model=OrganizationOut)
def get_my_organization(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    organization = _org_service.get_user_organization(db, current_user)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization linked to this account yet.",
        )
    return organization


@router.patch("/me", response_model=OrganizationOut)
def update_my_organization(
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    if not current_user.default_organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization linked to this account yet.",
        )
    try:
        return _org_service.update_organization(
            db,
            current_user,
            current_user.default_organization_id,
            name=body.name,
            slug=body.slug,
            status=body.status,
            settings=body.settings,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.get("/{organization_id}", response_model=OrganizationOut)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _org_service.get_organization_for_user(db, current_user, organization_id)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.patch("/{organization_id}", response_model=OrganizationOut)
def update_organization(
    organization_id: UUID,
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _org_service.update_organization(
            db,
            current_user,
            organization_id,
            name=body.name,
            slug=body.slug,
            status=body.status,
            settings=body.settings,
        )
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc


@router.delete("/{organization_id}", response_model=OrganizationOut)
def close_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    try:
        return _org_service.close_organization(db, current_user, organization_id)
    except (ValueError, PermissionError) as exc:
        raise _handle_service_error(exc) from exc
