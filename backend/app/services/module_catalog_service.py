from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit import AuditModuleCatalog
from app.repositories.module_catalog_repository import ModuleCatalogRepository


class ModuleCatalogService:
    def __init__(self, repository: ModuleCatalogRepository | None = None) -> None:
        self._repo = repository or ModuleCatalogRepository()

    def list_catalog(self, db: Session) -> list[AuditModuleCatalog]:
        return self._repo.list_active_modules(db)

    def get_module_by_code(self, db: Session, code: str) -> AuditModuleCatalog | None:
        return self._repo.get_by_code(db, code.strip().upper())
