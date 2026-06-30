"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  disableEngagementModule,
  enableEngagementModule,
  fetchEngagementModules,
  fetchModuleCatalog,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { ApiEngagementModule, ApiModuleCatalog } from "@/lib/api/types";
import {
  catalogStatusToUiStatus,
  hrefForModuleSlug,
} from "@/lib/dashboard/catalogUtils";
import { useAuth } from "@/lib/auth/AuthProvider";

const MANAGER_ROLES = new Set([
  "organization_owner",
  "audit_manager",
  "partner",
]);

interface EngagementModulesPanelProps {
  engagementId: string;
}

export function EngagementModulesPanel({ engagementId }: EngagementModulesPanelProps) {
  const { session } = useAuth();
  const [enabled, setEnabled] = useState<ApiEngagementModule[]>([]);
  const [catalog, setCatalog] = useState<ApiModuleCatalog[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canManage = MANAGER_ROLES.has(session?.user.memberRole ?? "");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [modules, cat] = await Promise.all([
        fetchEngagementModules(engagementId),
        fetchModuleCatalog(),
      ]);
      setEnabled(modules);
      setCatalog(cat);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setEnabled([]);
        try {
          setCatalog(await fetchModuleCatalog());
        } catch {
          setCatalog([]);
        }
      } else {
        setError(err instanceof Error ? err.message : "Failed to load modules");
      }
    } finally {
      setLoading(false);
    }
  }, [engagementId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleToggle(code: string, isCurrentlyEnabled: boolean) {
    setSaving(code);
    setError(null);
    try {
      if (isCurrentlyEnabled) {
        await disableEngagementModule(engagementId, code);
      } else {
        await enableEngagementModule(engagementId, code);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update module");
    } finally {
      setSaving(null);
    }
  }

  const enabledCodes = new Set(
    enabled.filter((m) => m.is_enabled).map((m) => m.module_code)
  );
  const builtModules = catalog.filter(
    (m) => catalogStatusToUiStatus(m.implementation_status) === "active"
  );

  return (
    <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-4">
      {loading && <p className="text-sm text-slate-500">Loading modules…</p>}
      {error && (
        <p className="mb-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading && enabledCodes.size === 0 && (
        <p className="mb-3 text-sm text-slate-500">
          No modules enabled yet. Create a project or enable modules below.
        </p>
      )}

      <div className="space-y-2">
        {enabled
          .filter((m) => m.is_enabled)
          .map((m) => (
            <div
              key={m.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">{m.module_name}</p>
                <p className="text-xs text-slate-500">{m.category}</p>
              </div>
              <Link
                href={hrefForModuleSlug(m.module_slug)}
                className="text-xs font-medium text-brand-600 hover:underline"
              >
                Open module →
              </Link>
            </div>
          ))}
      </div>

      {canManage && !loading && builtModules.length > 0 && (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Enable built modules
          </p>
          <div className="flex flex-wrap gap-2">
            {builtModules.map((item) => {
              const on = enabledCodes.has(item.code);
              return (
                <button
                  key={item.code}
                  type="button"
                  disabled={saving === item.code}
                  onClick={() => handleToggle(item.code, on)}
                  className={`rounded-full px-3 py-1 text-xs font-medium ring-1 transition ${
                    on
                      ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
                      : "bg-slate-50 text-slate-600 ring-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {saving === item.code ? "…" : on ? `✓ ${item.name}` : `+ ${item.name}`}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
