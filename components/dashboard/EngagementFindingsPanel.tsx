"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchEngagementFindings,
  updateFindingRemediation,
  updateFindingStatus,
} from "@/lib/api";
import type { ApiFindingLifecycle } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";

const STATUSES = [
  { value: "open", label: "Open" },
  { value: "under_review", label: "Under Review" },
  { value: "cleared", label: "Cleared" },
  { value: "accepted", label: "Accepted" },
  { value: "closed", label: "Closed" },
];

interface EngagementFindingsPanelProps {
  engagementId: string;
}

export function EngagementFindingsPanel({ engagementId }: EngagementFindingsPanelProps) {
  const { session } = useAuth();
  const role = session?.user.memberRole ?? "";
  const canApprove = ["organization_owner", "partner", "audit_manager", "reviewer"].includes(role);

  const [findings, setFindings] = useState<ApiFindingLifecycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchEngagementFindings(engagementId, {
        status: statusFilter || undefined,
        limit: 50,
      });
      setFindings(result.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load findings");
    } finally {
      setLoading(false);
    }
  }, [engagementId, statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStatusChange(findingId: string, status: string) {
    try {
      await updateFindingStatus(findingId, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    }
  }

  if (loading) {
    return (
      <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-6 text-sm text-slate-500">
        Loading findings…
      </div>
    );
  }

  return (
    <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">Findings Lifecycle</h3>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-200 px-2 py-1 text-xs"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </p>
      )}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Finding</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Risk</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Status</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Remediation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {findings.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-4 text-center text-slate-500">
                  No findings for this engagement. Run analysis on a module project first.
                </td>
              </tr>
            ) : (
              findings.map((f) => (
                <tr key={f.id}>
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-900">{f.finding_title}</div>
                    <div className="text-slate-500">{f.rule_code}</div>
                  </td>
                  <td className="px-3 py-2 capitalize text-slate-600">{f.risk_level}</td>
                  <td className="px-3 py-2">
                    <select
                      value={f.status}
                      disabled={
                        !canApprove &&
                        ["cleared", "accepted", "closed"].includes(f.status)
                      }
                      onChange={(e) => handleStatusChange(f.id, e.target.value)}
                      className="rounded border border-slate-200 px-2 py-1 text-xs capitalize"
                    >
                      {STATUSES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2 capitalize text-slate-600">
                    {f.remediation_status.replace(/_/g, " ")}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
