"use client";

import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type { ApiAuditFinding } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

interface AuditFindingsPanelProps {
  findings: ApiAuditFinding[];
}

const RISK_STYLES: Record<string, string> = {
  high: "bg-red-50 text-red-700 ring-red-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export function AuditFindingsPanel({ findings }: AuditFindingsPanelProps) {
  if (!findings.length) {
    return (
      <SectionCard
        title="Audit Findings Summary"
        description="Grouped findings by rule for the audit file."
      >
        <p className="text-sm text-slate-500">No audit findings generated.</p>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Audit Findings Summary"
      description="Grouped findings by rule — suitable for working papers and management letters."
    >
      <ul className="space-y-4" role="list">
        {findings.map((f) => (
          <li
            key={f.id}
            className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-600 dark:bg-slate-800/40"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-slate-900 dark:text-white">
                  {f.finding_title}
                </p>
                <p className="mt-0.5 text-xs font-mono text-slate-500">{f.rule_code}</p>
              </div>
              <span
                className={cn(
                  "rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1",
                  RISK_STYLES[f.risk_level] ?? RISK_STYLES.low
                )}
              >
                {f.risk_level} · {f.affected_count} entries
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {f.observation}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              <span className="font-medium">Recommendation:</span> {f.recommendation}
            </p>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
