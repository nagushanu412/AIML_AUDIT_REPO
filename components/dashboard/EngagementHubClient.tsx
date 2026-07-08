"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  approveAnalysisRun,
  archiveAnalysisRun,
  createAnalysisRun,
  designateOfficialAnalysisRun,
  fetchEngagementHub,
  generateEngagementReport,
  returnAnalysisRunToAuditor,
  startAnalysisRun,
  submitAnalysisRunForReview,
} from "@/lib/api";
import type { ApiAnalysisRun, ApiEngagementHub } from "@/lib/api/types";
import { Button } from "@/components/ui/Button";
import { hrefForModuleSlug } from "@/lib/dashboard/catalogUtils";

interface EngagementHubClientProps {
  engagementId: string;
}

function statusBadgeClass(status: string): string {
  if (status === "locked" || status === "approved") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (status === "under_review") {
    return "bg-amber-100 text-amber-800";
  }
  if (status === "running") {
    return "bg-blue-100 text-blue-800";
  }
  if (status === "archived") {
    return "bg-slate-200 text-slate-600";
  }
  return "bg-slate-100 text-slate-700";
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

  async function handleRunAction(
    action: (engagementId: string, runId: string) => Promise<ApiAnalysisRun>,
    runId: string
  ) {
    setSaving(true);
    try {
      await action(engagementId, runId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
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

      {hub.official_runs.length > 0 && (
        <section className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-emerald-900">Official Runs</h2>
          <div className="mt-3 space-y-2 text-xs">
            {hub.official_runs.map((run) => (
              <div
                key={run.id}
                className="flex justify-between rounded border border-emerald-100 bg-white px-3 py-2"
              >
                <span>
                  <span className="mr-2 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-white">
                    Official
                  </span>
                  {run.run_name} · {run.module_code}
                </span>
                <span className={`rounded px-2 py-0.5 capitalize ${statusBadgeClass(run.status)}`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        </section>
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
                className="rounded border border-slate-100 px-3 py-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    {run.is_official && (
                      <span className="mr-2 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-white">
                        Official
                      </span>
                    )}
                    {run.run_name} · {run.module_code}
                  </span>
                  <span className={`rounded px-2 py-0.5 capitalize ${statusBadgeClass(run.status)}`}>
                    {run.status}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {run.status === "completed" && (
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => handleRunAction(submitAnalysisRunForReview, run.id)}
                      className="text-brand-600 hover:underline"
                    >
                      Submit for review
                    </button>
                  )}
                  {run.status === "under_review" && (
                    <>
                      <button
                        type="button"
                        disabled={saving}
                        onClick={() => handleRunAction(approveAnalysisRun, run.id)}
                        className="text-brand-600 hover:underline"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={saving}
                        onClick={() => handleRunAction(returnAnalysisRunToAuditor, run.id)}
                        className="text-slate-600 hover:underline"
                      >
                        Return to auditor
                      </button>
                    </>
                  )}
                  {(run.status === "locked" || run.status === "approved") && !run.is_official && (
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => handleRunAction(designateOfficialAnalysisRun, run.id)}
                      className="text-emerald-700 hover:underline"
                    >
                      Designate official
                    </button>
                  )}
                  {(run.status === "locked" || run.status === "approved") && (
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => handleRunAction(archiveAnalysisRun, run.id)}
                      className="text-slate-600 hover:underline"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
