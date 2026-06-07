import { AlertTriangle, BarChart3, CheckCircle, ShieldAlert } from "lucide-react";
import type { AnalysisSummary } from "@/lib/journal-entry-testing/types";
import { formatRecordCount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface ResultsSummaryCardsProps {
  summary: AnalysisSummary | null;
}

const CARDS: {
  key: keyof AnalysisSummary;
  label: string;
  icon: typeof BarChart3;
  color: string;
}[] = [
  {
    key: "totalEntries",
    label: "Total Entries",
    icon: BarChart3,
    color: "bg-brand-50 text-brand-600 ring-brand-100 dark:bg-brand-950/50 dark:text-brand-400 dark:ring-brand-900",
  },
  {
    key: "highRisk",
    label: "High Risk Entries",
    icon: ShieldAlert,
    color: "bg-red-50 text-red-600 ring-red-100 dark:bg-red-950/50 dark:text-red-400 dark:ring-red-900",
  },
  {
    key: "mediumRisk",
    label: "Medium Risk Entries",
    icon: AlertTriangle,
    color: "bg-amber-50 text-amber-600 ring-amber-100 dark:bg-amber-950/50 dark:text-amber-400 dark:ring-amber-900",
  },
  {
    key: "lowRisk",
    label: "Low Risk Entries",
    icon: CheckCircle,
    color: "bg-emerald-50 text-emerald-600 ring-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-900",
  },
];

export function ResultsSummaryCards({ summary }: ResultsSummaryCardsProps) {
  if (!summary) return null;

  return (
    <section aria-label="Analysis results summary">
      <h2 className="mb-4 font-display text-base font-semibold text-slate-900 dark:text-white">
        Results Dashboard
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {CARDS.map(({ key, label, icon: Icon, color }) => (
          <article
            key={key}
            className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/80 dark:bg-slate-900"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  {label}
                </p>
                <p className="mt-2 font-display text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {formatRecordCount(summary[key])}
                </p>
              </div>
              <div
                className={cn(
                  "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ring-1",
                  color
                )}
              >
                <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden="true" />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
