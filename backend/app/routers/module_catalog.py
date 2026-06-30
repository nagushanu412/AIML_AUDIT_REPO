from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.module_catalog import ModuleCatalogOut
from app.services.module_catalog_service import ModuleCatalogService

router = APIRouter(prefix="/modules", tags=["Module Catalog"])
_catalog_service = ModuleCatalogService()


@router.get("/catalog", response_model=list[ModuleCatalogOut])
def list_module_catalog(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    del current_user
    return _catalog_service.list_catalog(db)
