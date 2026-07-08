"use client";

import { useEffect, useState } from "react";

export type ModuleWorkspaceConfig = {
  module_code: string;
  metadata: {
    code: string;
    name: string;
    project_type: string;
    slug: string;
    category: string;
    icon: string;
    implementation_status: string;
    input_format: string;
    rule_prefix: string;
    theme_color: string;
    ui_config: Record<string, unknown>;
    plugin_config: Record<string, unknown>;
  };
  pipeline_steps: string[];
  supported_endpoints: string[];
};

type AuditModuleWorkspaceProps = {
  moduleCode: string;
  apiBaseUrl?: string;
  children?: React.ReactNode;
};

/**
 * Generic module workspace shell — Phase 3 M1.
 * Existing module UIs remain unchanged; this shell is used when modules
 * are migrated to the generic framework in Milestone 2.
 */
export function AuditModuleWorkspace({
  moduleCode,
  apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  children,
}: AuditModuleWorkspaceProps) {
  const [config, setConfig] = useState<ModuleWorkspaceConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${apiBaseUrl}/modules/${encodeURIComponent(moduleCode)}/workspace-config`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? `Failed to load workspace config (${res.status})`);
        }
        return res.json() as Promise<ModuleWorkspaceConfig>;
      })
      .then((data) => {
        if (!cancelled) {
          setConfig(data);
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setConfig(null);
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, moduleCode]);

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-slate-600">
        Loading module workspace…
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center text-red-700">
        {error ?? "Module workspace unavailable."}
      </div>
    );
  }

  return (
    <div className="space-y-6" data-module={config.module_code}>
      <header className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
          Generic Module Workspace
        </p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-900">{config.metadata.name}</h1>
        <p className="mt-2 text-sm text-slate-600">{config.metadata.category}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {config.pipeline_steps.map((step) => (
            <span
              key={step}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
            >
              {step}
            </span>
          ))}
        </div>
      </header>
      {children ?? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
          Module-specific panels will render here in Milestone 2.
        </div>
      )}
    </div>
  );
}
