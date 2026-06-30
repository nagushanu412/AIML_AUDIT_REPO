from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.models.audit import AuditProject
from app.schemas.hierarchy import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.engagement_module_service import EngagementModuleService
from app.services.project_access import get_owned_engagement, get_owned_project, project_list_query
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    engagement_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    query = project_list_query(db, tenant)
    if engagement_id:
        get_owned_engagement(db, engagement_id, tenant)
        query = query.filter(AuditProject.engagement_id == engagement_id)
    return query.order_by(AuditProject.name).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    get_owned_engagement(db, body.engagement_id, tenant)
    project = AuditProject(**body.model_dump())
    db.add(project)
    db.flush()
    EngagementModuleService().sync_from_project_type(
        db, body.engagement_id, body.project_type, tenant.user.id
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    return get_owned_project(db, project_id, tenant)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    project = get_owned_project(db, project_id, tenant)
    db.delete(project)
    db.commit()
