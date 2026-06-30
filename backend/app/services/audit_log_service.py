from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditLogService:
    def write_log(
        self,
        db: Session,
        *,
        action: str,
        entity_type: str,
        user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        commit: bool = True,
    ) -> AuditLog:
        entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        else:
            db.flush()
        return entry

    def list_for_organization(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
