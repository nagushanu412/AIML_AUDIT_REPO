import type { ApiModuleCatalog } from "@/lib/api/types";
import { resolveModuleIcon } from "@/lib/dashboard/moduleIcons";
import type { AuditModule, ModuleStatus } from "@/lib/dashboard/types";

export function catalogStatusToUiStatus(
  implementationStatus: string
): ModuleStatus {
  return implementationStatus === "built" || implementationStatus === "beta"
    ? "active"
    : "coming_soon";
}

export function mapCatalogToAuditModule(item: ApiModuleCatalog): AuditModule {
  return {
    id: item.slug,
    name: item.name,
    description: item.description ?? "",
    status: catalogStatusToUiStatus(item.implementation_status),
    slug: item.slug,
    icon: resolveModuleIcon(item.icon),
    category: item.category,
  };
}

export function mapCatalogList(items: ApiModuleCatalog[]): AuditModule[] {
  return items.map(mapCatalogToAuditModule);
}

export function moduleHref(slug: string): string {
  return `/dashboard/ai-modules/${slug}`;
}

export function hrefForModuleSlug(slug: string): string {
  if (slug === "journal-entry-testing") {
    return "/dashboard/ai-modules/journal-entry-testing";
  }
  return moduleHref(slug);
}

export function moduleOpenHref(module: AuditModule): string {
  return hrefForModuleSlug(module.slug);
}
