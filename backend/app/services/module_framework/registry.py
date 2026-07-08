"""Module registry — resolves plugins by module code."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditModuleCatalog, EngagementEnabledModule, ModulePluginConfig
from app.repositories.module_catalog_repository import ModuleCatalogRepository
from app.services.module_framework.plugins import PLUGIN_BUILDERS
from app.services.module_framework.protocol import ModuleMetadata, ModuleProvider
from app.services.tenant_context import TenantContext


class ModuleNotFoundError(ValueError):
    pass


class ModuleNotBuiltError(ValueError):
    pass


class ModuleRegistry:
    def __init__(self, catalog_repo: ModuleCatalogRepository | None = None) -> None:
        self._catalog = catalog_repo or ModuleCatalogRepository()
        self._static_providers: dict[str, ModuleProvider] = {}

    def register_static(self, provider: ModuleProvider) -> None:
        self._static_providers[provider.code.upper()] = provider

    def get_catalog_row(self, db: Session, module_code: str) -> AuditModuleCatalog:
        module = self._catalog.get_by_code(db, module_code.strip().upper())
        if not module:
            raise ModuleNotFoundError(f"Module '{module_code}' not found in catalog.")
        return module

    def get_plugin_config(
        self, db: Session, module_code: str
    ) -> ModulePluginConfig | None:
        return (
            db.query(ModulePluginConfig)
            .filter(
                ModulePluginConfig.module_code == module_code.strip().upper(),
                ModulePluginConfig.is_active.is_(True),
            )
            .first()
        )

    def build_metadata(
        self, module: AuditModuleCatalog, plugin_config: ModulePluginConfig | None
    ) -> ModuleMetadata:
        config = plugin_config.config if plugin_config else {}
        return ModuleMetadata(
            code=module.code,
            name=module.name,
            project_type=module.project_type or "",
            slug=module.slug,
            category=module.category,
            icon=module.icon,
            implementation_status=module.implementation_status,
            input_format=module.input_format or "xlsx",
            rule_prefix=module.rule_prefix or "",
            theme_color=module.theme_color or "blue",
            ui_config=module.ui_config or {},
            plugin_config=config,
        )

    def resolve_provider(self, db: Session, module_code: str) -> ModuleProvider:
        code = module_code.strip().upper()
        if code in self._static_providers:
            return self._static_providers[code]

        module = self.get_catalog_row(db, code)
        if module.implementation_status not in ("built", "beta"):
            raise ModuleNotBuiltError(
                f"Module '{code}' is not yet implemented (status: {module.implementation_status})."
            )

        builder = PLUGIN_BUILDERS.get(code)
        if not builder:
            raise ModuleNotBuiltError(f"No plugin registered for module '{code}'.")

        plugin_config = self.get_plugin_config(db, code)
        metadata = self.build_metadata(module, plugin_config)
        provider = builder(metadata)
        self._static_providers[code] = provider
        return provider

    def list_modules(
        self, db: Session, tenant: TenantContext | None = None
    ) -> list[AuditModuleCatalog]:
        del tenant
        return (
            db.query(AuditModuleCatalog)
            .filter(AuditModuleCatalog.is_active.is_(True))
            .order_by(AuditModuleCatalog.display_order)
            .all()
        )

    def is_enabled_for_engagement(
        self, db: Session, engagement_id: uuid.UUID, module_code: str
    ) -> bool:
        module = self.get_catalog_row(db, module_code)
        row = (
            db.query(EngagementEnabledModule)
            .filter(
                EngagementEnabledModule.engagement_id == engagement_id,
                EngagementEnabledModule.module_catalog_id == module.id,
                EngagementEnabledModule.is_enabled.is_(True),
            )
            .first()
        )
        return row is not None


_registry: ModuleRegistry | None = None


def get_module_registry() -> ModuleRegistry:
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry
