import { AlertTriangle, BarChart3, CheckCircle, ShieldAlert } from "lucide-react";
import type { ProcurementAnalysisSummary } from "@/lib/procurement-testing/types";
import { formatRecordCount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface ProcurementResultsSummaryCardsProps {
  summary: ProcurementAnalysisSummary | null;
}

const CARDS = [
  { key: "totalInvoices" as const, label: "Total Invoices", icon: BarChart3, color: "bg-teal-50 text-teal-600 ring-teal-100" },
  { key: "highRisk" as const, label: "High Risk", icon: ShieldAlert, color: "bg-red-50 text-red-600 ring-red-100" },
  { key: "mediumRisk" as const, label: "Medium Risk", icon: AlertTriangle, color: "bg-amber-50 text-amber-600 ring-amber-100" },
  { key: "lowRisk" as const, label: "Low Risk", icon: CheckCircle, color: "bg-emerald-50 text-emerald-600 ring-emerald-100" },
];

export function ProcurementResultsSummaryCards({ summary }: ProcurementResultsSummaryCardsProps) {
  if (!summary) return null;

  return (
    <section aria-label="Procurement analysis results">
      <h2 className="mb-4 font-display text-base font-semibold text-slate-900">Procurement Results Dashboard</h2>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {CARDS.map(({ key, label, icon: Icon, color }) => (
          <article key={key} className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500">{label}</p>
                <p className="mt-2 font-display text-3xl font-bold text-slate-900">
                  {formatRecordCount(summary[key])}
                </p>
              </div>
              <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl ring-1", color)}>
                <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden="true" />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
