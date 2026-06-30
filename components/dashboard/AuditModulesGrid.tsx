"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchModuleCatalog } from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import { mapCatalogList } from "@/lib/dashboard/catalogUtils";
import { AUDIT_MODULES } from "@/lib/dashboard/modules";
import type { AuditModule } from "@/lib/dashboard/types";
import { AuditModuleCard } from "@/components/dashboard/AuditModuleCard";

export function AuditModulesGrid() {
  const [modules, setModules] = useState<AuditModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fromApi, setFromApi] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const catalog = await fetchModuleCatalog();
      setModules(mapCatalogList(catalog));
      setFromApi(true);
    } catch (err) {
      setModules(AUDIT_MODULES);
      setFromApi(false);
      if (!(err instanceof ApiError && err.status === 401)) {
        setError(
          err instanceof Error ? err.message : "Could not load module catalog"
        );
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const activeCount = modules.filter((m) => m.status === "active").length;
  const comingSoonCount = modules.length - activeCount;

  if (loading) {
    return <p className="text-sm text-slate-500">Loading module catalog…</p>;
  }

  return (
    <div>
      {error && (
        <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error} — showing cached catalog.
        </p>
      )}

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
          {activeCount} Active
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
          {comingSoonCount} Coming Soon
        </span>
        <span className="text-sm text-slate-500">
          {modules.length} audit modules available
        </span>
        {fromApi && (
          <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700 ring-1 ring-brand-100">
            Live catalog
          </span>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        {modules.map((module) => (
          <AuditModuleCard key={module.id} module={module} />
        ))}
      </div>
    </div>
  );
}
