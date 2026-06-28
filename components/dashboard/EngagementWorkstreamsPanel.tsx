import Link from "next/link";
import { ArrowRight, BookOpen, Receipt, ShoppingCart } from "lucide-react";
import { WORKSTREAM_CONFIG, formatModuleList, getModulesForProjectType } from "@/lib/dashboard/projectModuleMap";

const WORKSTREAMS = [
  {
    key: "journal" as const,
    title: "Journal Testing",
    href: "/dashboard/ai-modules/journal-entry-testing",
    icon: BookOpen,
    status: "Active",
    statusClass: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    modules: formatModuleList(getModulesForProjectType("journal_testing")),
    note: "Upload journal entries and run 7-rule AI analysis.",
  },
  {
    key: "revenue" as const,
    title: WORKSTREAM_CONFIG.revenue_testing.title,
    href: WORKSTREAM_CONFIG.revenue_testing.href,
    icon: Receipt,
    status: "Active",
    statusClass: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    modules: formatModuleList(getModulesForProjectType("revenue_testing")),
    note: "Upload sales register, run 7 revenue rules, export working papers.",
  },
  {
    key: "procurement" as const,
    title: WORKSTREAM_CONFIG.procurement_testing.title,
    href: WORKSTREAM_CONFIG.procurement_testing.href,
    icon: ShoppingCart,
    status: "Active",
    statusClass: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    modules: formatModuleList(getModulesForProjectType("procurement_testing")),
    note: "Upload vendor register, run 7 procurement rules, export working papers.",
  },
];

export function EngagementWorkstreamsPanel() {
  return (
    <div className="mb-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">Engagement workstreams</h2>
      <p className="mt-1 text-sm text-slate-600">
        Each engagement project type opens its own workspace. Journal testing is separate from
        revenue and procurement.
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {WORKSTREAMS.map((ws) => {
          const Icon = ws.icon;
          return (
            <Link
              key={ws.key}
              href={ws.href}
              className="group rounded-lg border border-slate-200 p-4 transition hover:border-brand-300 hover:shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                  <Icon className="h-5 w-5" />
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${ws.statusClass}`}
                >
                  {ws.status}
                </span>
              </div>
              <p className="mt-3 font-medium text-slate-900">{ws.title}</p>
              <p className="mt-1 text-xs text-slate-500">{ws.modules}</p>
              <p className="mt-2 text-xs text-slate-600">{ws.note}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-brand-600 group-hover:underline">
                Open workspace
                <ArrowRight className="h-3 w-3" />
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
