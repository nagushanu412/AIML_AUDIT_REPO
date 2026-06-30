"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  createAnalysisRun,
  fetchEngagementHub,
  generateEngagementReport,
  startAnalysisRun,
} from "@/lib/api";
import type { ApiEngagementHub } from "@/lib/api/types";
import { Button } from "@/components/ui/Button";
import { hrefForModuleSlug } from "@/lib/dashboard/catalogUtils";

interface EngagementHubClientProps {
  engagementId: string;
}

export function EngagementHubClient({ engagementId }: EngagementHubClientProps) {
  const [hub, setHub] = useState<ApiEngagementHub | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHub(await fetchEngagementHub(engagementId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load engagement hub");
    } finally {
      setLoading(false);
    }
  }, [engagementId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStartModule(moduleCode: string) {
    setSaving(true);
    try {
      const run = await createAnalysisRun(engagementId, { module_code: moduleCode });
      await startAnalysisRun(engagementId, run.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateReport() {
    setSaving(true);
    try {
      await generateEngagementReport(engagementId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading engagement hub…</p>;
  }

  if (!hub) {
    return <p className="text-sm text-red-600">{error ?? "Engagement not found"}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">{hub.financial_year}</h1>
        <p className="mt-1 text-sm text-slate-500 capitalize">
          Status: {hub.status} · {hub.findings_count} findings
        </p>
        {hub.pending_actions.length > 0 && (
          <ul className="mt-3 list-disc pl-5 text-sm text-amber-800">
            {hub.pending_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        )}
      </div>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Enabled Modules</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {hub.enabled_modules.map((mod) => (
            <div
              key={mod.module_code}
              className="rounded-lg border border-slate-100 p-3"
            >
              <div className="font-medium text-slate-900">{mod.module_name}</div>
              <div className="mt-2 flex flex-wrap gap-2">
                <Link
                  href={hrefForModuleSlug(mod.module_slug)}
                  className="text-xs text-brand-600 hover:underline"
                >
                  Open module
                </Link>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleStartModule(mod.module_code)}
                  className="text-xs text-brand-600 hover:underline"
                >
                  Start run
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Analysis Runs</h2>
          <Button
            type="button"
            variant="primary"
            size="sm"
            isLoading={saving}
            onClick={handleGenerateReport}
          >
            Generate Report
          </Button>
        </div>
        <div className="mt-3 space-y-2 text-xs">
          {hub.latest_runs.length === 0 ? (
            <p className="text-slate-500">No analysis runs yet.</p>
          ) : (
            hub.latest_runs.map((run) => (
              <div
                key={run.id}
                className="flex justify-between rounded border border-slate-100 px-3 py-2"
              >
                <span>
                  {run.run_name} · {run.module_code}
                </span>
                <span className="capitalize text-slate-600">{run.status}</span>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
