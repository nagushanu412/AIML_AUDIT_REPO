from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditModuleCatalog, AuditProject, EngagementEnabledModule, ModuleAnalysisRun
from app.repositories.module_catalog_repository import ModuleCatalogRepository
from app.services.analysis_run_service import SUGGESTED_RUN_NAMES
from app.services.member_constants import role_has_permission
from app.services.module_catalog_constants import (
    MODULE_CODE_TO_PROJECT_TYPE,
    MODULE_CODE_TO_NAME,
    PROJECT_TYPE_TO_MODULE_CODE,
)
from app.services.project_access import get_owned_engagement
from app.services.tenant_context import TenantContext


class EngagementModuleService:
    def __init__(self, catalog_repo: ModuleCatalogRepository | None = None) -> None:
        self._catalog_repo = catalog_repo or ModuleCatalogRepository()

    def list_enabled_modules(
        self, db: Session, tenant: TenantContext, engagement_id: uuid.UUID
    ) -> list[dict]:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        rows = (
            db.query(EngagementEnabledModule)
            .options(joinedload(EngagementEnabledModule.module))
            .filter(
                EngagementEnabledModule.engagement_id == engagement.id,
                EngagementEnabledModule.is_enabled.is_(True),
            )
            .order_by(EngagementEnabledModule.created_at)
            .all()
        )
        return [self._row_to_dict(row) for row in rows if row.module]

    def enable_module(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        module_code: str,
    ) -> dict:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        module = self._catalog_repo.get_by_code(db, module_code.strip().upper())
        if not module:
            raise ValueError(f"Module '{module_code}' not found in catalog.")

        self._assert_plan_allows_module(db, tenant, module.code)

        existing = (
            db.query(EngagementEnabledModule)
            .filter(
                EngagementEnabledModule.engagement_id == engagement.id,
                EngagementEnabledModule.module_catalog_id == module.id,
            )
            .first()
        )
        now = datetime.now(timezone.utc)
        if existing:
            existing.is_enabled = True
            existing.enabled_at = now
            existing.enabled_by = tenant.user.id
            row = existing
        else:
            row = EngagementEnabledModule(
                engagement_id=engagement.id,
                module_catalog_id=module.id,
                is_enabled=True,
                enabled_at=now,
                enabled_by=tenant.user.id,
            )
            db.add(row)

        db.commit()
        db.refresh(row)
        row.module = module
        self._ensure_module_workspace(db, engagement, module, tenant)
        db.commit()
        return self._row_to_dict(row)

    def disable_module(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        module_code: str,
    ) -> dict:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        module = self._catalog_repo.get_by_code(db, module_code.strip().upper())
        if not module:
            raise ValueError(f"Module '{module_code}' not found in catalog.")

        row = (
            db.query(EngagementEnabledModule)
            .options(joinedload(EngagementEnabledModule.module))
            .filter(
                EngagementEnabledModule.engagement_id == engagement.id,
                EngagementEnabledModule.module_catalog_id == module.id,
            )
            .first()
        )
        if not row:
            raise ValueError("Module is not enabled on this engagement.")

        row.is_enabled = False
        db.commit()
        db.refresh(row)
        return self._row_to_dict(row)

    def sync_from_project_type(
        self,
        db: Session,
        engagement_id: uuid.UUID,
        project_type: str,
        user_id: uuid.UUID,
    ) -> None:
        code = PROJECT_TYPE_TO_MODULE_CODE.get(project_type)
        if not code:
            return
        module = self._catalog_repo.get_by_code(db, code)
        if not module:
            return
        existing = (
            db.query(EngagementEnabledModule)
            .filter(
                EngagementEnabledModule.engagement_id == engagement_id,
                EngagementEnabledModule.module_catalog_id == module.id,
            )
            .first()
        )
        if existing:
            if not existing.is_enabled:
                existing.is_enabled = True
            return
        db.add(
            EngagementEnabledModule(
                engagement_id=engagement_id,
                module_catalog_id=module.id,
                is_enabled=True,
                enabled_by=user_id,
            )
        )

    def _ensure_module_workspace(
        self,
        db: Session,
        engagement,
        module: AuditModuleCatalog,
        tenant: TenantContext,
    ) -> None:
        """Auto-create legacy project + draft analysis run when a module is enabled."""
        project_type = MODULE_CODE_TO_PROJECT_TYPE.get(module.code)
        project = None
        if project_type:
            project = (
                db.query(AuditProject)
                .filter(
                    AuditProject.engagement_id == engagement.id,
                    AuditProject.project_type == project_type,
                )
                .first()
            )
            if not project:
                project = AuditProject(
                    engagement_id=engagement.id,
                    name=MODULE_CODE_TO_NAME.get(module.code, module.name),
                    project_type=project_type,
                    status="active",
                )
                db.add(project)
                db.flush()
        else:
            project = (
                db.query(AuditProject)
                .filter(AuditProject.engagement_id == engagement.id)
                .first()
            )

        existing_draft = (
            db.query(ModuleAnalysisRun)
            .filter(
                ModuleAnalysisRun.engagement_id == engagement.id,
                ModuleAnalysisRun.module_catalog_id == module.id,
                ModuleAnalysisRun.status == "draft",
            )
            .first()
        )
        if not existing_draft:
            db.add(
                ModuleAnalysisRun(
                    engagement_id=engagement.id,
                    project_id=project.id if project else None,
                    module_catalog_id=module.id,
                    organization_id=engagement.organization_id or tenant.organization_id,
                    run_name=SUGGESTED_RUN_NAMES[0],
                    status="draft",
                    run_owner_id=tenant.user.id,
                )
            )

    @staticmethod
    def _assert_can_manage(tenant: TenantContext) -> None:
        role = tenant.member_role or ""
        if not (
            role_has_permission(role, "organization.update")
            or role in {"organization_owner", "audit_manager", "partner"}
        ):
            raise PermissionError("You do not have permission to manage engagement modules.")

    @staticmethod
    def _assert_plan_allows_module(db: Session, tenant: TenantContext, module_code: str) -> None:
        if not tenant.organization_id:
            return
        from app.repositories.subscription_repository import SubscriptionRepository

        sub = SubscriptionRepository().get_active_subscription(db, tenant.organization_id)
        if not sub or not sub.plan:
            return
        allowed = sub.plan.enabled_module_codes or []
        if allowed and module_code not in allowed:
            raise ValueError(
                f"Module '{module_code}' is not included in your subscription plan."
            )

    @staticmethod
    def _row_to_dict(row: EngagementEnabledModule) -> dict:
        module = row.module
        return {
            "id": row.id,
            "engagement_id": row.engagement_id,
            "module_code": module.code if module else "",
            "module_name": module.name if module else "",
            "module_slug": module.slug if module else "",
            "category": module.category if module else "",
            "implementation_status": module.implementation_status if module else "",
            "is_enabled": row.is_enabled,
            "enabled_at": row.enabled_at,
        }
