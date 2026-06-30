"use client";

import { useCallback, useEffect, useState } from "react";
import {
  changeSubscriptionPlan,
  fetchMySubscription,
  fetchSubscriptionPlans,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { ApiSubscriptionPlan, ApiSubscriptionSummary } from "@/lib/api/types";

function formatBytes(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)} MB`;
  return `${bytes} B`;
}

function UsageRow({
  label,
  used,
  limit,
}: {
  label: string;
  used: number;
  limit: number;
}) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-900">
          {used.toLocaleString()} / {limit.toLocaleString()}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-brand-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function SubscriptionSettings() {
  const [summary, setSummary] = useState<ApiSubscriptionSummary | null>(null);
  const [plans, setPlans] = useState<ApiSubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [changing, setChanging] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [plansData, summaryData] = await Promise.all([
        fetchSubscriptionPlans(),
        fetchMySubscription(),
      ]);
      setPlans(plansData);
      setSummary(summaryData);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setSummary(null);
        setPlans(await fetchSubscriptionPlans().catch(() => []));
      } else {
        setError(err instanceof Error ? err.message : "Failed to load subscription");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleChangePlan(planCode: string) {
    setChanging(planCode);
    setError(null);
    setSuccess(null);
    try {
      const updated = await changeSubscriptionPlan(planCode);
      setSummary(updated);
      setSuccess(`Plan changed to ${updated.plan.name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to change plan");
    } finally {
      setChanging(null);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading subscription…</p>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {success}
        </p>
      )}

      {!summary ? (
        <div className="max-w-lg rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900">Subscription</h2>
          <p className="mt-2 text-sm text-slate-600">
            Create an audit firm organization first. New organizations receive the{" "}
            <strong>Free</strong> plan automatically.
          </p>
        </div>
      ) : (
        <div className="max-w-3xl rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-900">Subscription & usage</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Current plan:{" "}
              <span className="font-medium capitalize text-slate-800">
                {summary.plan.name}
              </span>{" "}
              ({summary.subscription.status})
            </p>
          </div>
          <div className="space-y-4 px-5 py-4">
            <UsageRow
              label="Users"
              used={summary.usage.users}
              limit={summary.limits.max_users}
            />
            <UsageRow
              label="Clients"
              used={summary.usage.clients}
              limit={summary.limits.max_clients}
            />
            <UsageRow
              label="Engagements"
              used={summary.usage.engagements}
              limit={summary.limits.max_engagements}
            />
            <UsageRow
              label="Reports"
              used={summary.usage.reports}
              limit={summary.limits.max_reports}
            />
            <dl className="grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3 text-sm">
              <div>
                <dt className="text-slate-500">Monthly uploads</dt>
                <dd className="font-medium text-slate-900">
                  {summary.usage.uploads} / {summary.limits.monthly_uploads}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Storage</dt>
                <dd className="font-medium text-slate-900">
                  {formatBytes(summary.usage.storage_bytes)} /{" "}
                  {formatBytes(summary.limits.max_storage_bytes)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">AI credits / month</dt>
                <dd className="font-medium text-slate-900">
                  {summary.usage.ai_credits} / {summary.limits.monthly_ai_credits}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Support</dt>
                <dd className="font-medium capitalize text-slate-900">
                  {summary.plan.support_level}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      )}

      {plans.length > 0 && (
        <div className="max-w-3xl">
          <h3 className="mb-3 text-sm font-semibold text-slate-900">Available plans</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {plans.map((plan) => {
              const isCurrent = summary?.plan.code === plan.code;
              return (
                <div
                  key={plan.id}
                  className={`rounded-xl border p-4 ${
                    isCurrent
                      ? "border-brand-300 bg-brand-50/40 ring-1 ring-brand-200"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-900">{plan.name}</p>
                      <p className="mt-1 text-xs text-slate-500">{plan.description}</p>
                    </div>
                    {isCurrent && (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                        Current
                      </span>
                    )}
                  </div>
                  <ul className="mt-3 space-y-1 text-xs text-slate-600">
                    <li>{plan.max_users} users</li>
                    <li>{plan.max_clients} clients</li>
                    <li>{plan.max_engagements} engagements</li>
                    <li>{plan.enabled_module_codes.length} modules</li>
                  </ul>
                  {!isCurrent && summary && (
                    <button
                      type="button"
                      disabled={changing !== null}
                      onClick={() => handleChangePlan(plan.code)}
                      className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-50"
                    >
                      {changing === plan.code ? "Switching…" : `Switch to ${plan.name}`}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Plan changes are manual in this milestone. Billing integration arrives in a later
            phase.
          </p>
        </div>
      )}
    </div>
  );
}
