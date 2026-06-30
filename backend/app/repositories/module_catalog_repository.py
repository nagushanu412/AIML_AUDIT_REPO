from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit import AuditModuleCatalog


class ModuleCatalogRepository:
    def list_active_modules(self, db: Session) -> list[AuditModuleCatalog]:
        return (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.is_active.is_(True))
            .order_by(AuditModuleCatalog.display_order)
            .all()
        )

    def get_by_code(self, db: Session, code: str) -> AuditModuleCatalog | None:
        return (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.code == code, AuditModuleCatalog.is_active.is_(True))
            .first()
        )

    def count_active(self, db: Session) -> int:
        return (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.is_active.is_(True))
            .count()
        )
