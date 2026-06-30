from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.engagement_module import EngagementModuleOut
from app.services.engagement_module_service import EngagementModuleService
from app.services.tenant_context import TenantContext

router = APIRouter(prefix="/engagements", tags=["Engagement Modules"])
_module_service = EngagementModuleService()


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.get("/{engagement_id}/modules", response_model=list[EngagementModuleOut])
def list_engagement_modules(
    engagement_id: UUID,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        return _module_service.list_enabled_modules(db, tenant, engagement_id)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/modules/{module_code}/enable",
    response_model=EngagementModuleOut,
    status_code=status.HTTP_201_CREATED,
)
def enable_engagement_module(
    engagement_id: UUID,
    module_code: str,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        return _module_service.enable_module(db, tenant, engagement_id, module_code)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc


@router.post(
    "/{engagement_id}/modules/{module_code}/disable",
    response_model=EngagementModuleOut,
)
def disable_engagement_module(
    engagement_id: UUID,
    module_code: str,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    try:
        return _module_service.disable_module(db, tenant, engagement_id, module_code)
    except (ValueError, PermissionError) as exc:
        raise _handle_error(exc) from exc
