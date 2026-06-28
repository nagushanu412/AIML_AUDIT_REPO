import Link from "next/link";
import { ArrowLeft, Building2, Receipt } from "lucide-react";
import { MODULE_DESCRIPTION, MODULE_TITLE } from "@/lib/revenue-testing/constants";

export function RevenueModuleHeader() {
  return (
    <div className="mb-6 overflow-hidden rounded-2xl border border-indigo-200/60 bg-gradient-to-br from-white via-indigo-50/40 to-violet-50/30 shadow-sm dark:border-indigo-900/40 dark:from-slate-900 dark:via-indigo-950/20 dark:to-violet-950/20">
      <div className="border-b border-indigo-100/80 bg-indigo-600/5 px-5 py-2 dark:border-indigo-900/50">
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-700 dark:text-indigo-300">
          Enterprise Audit Workstream
        </p>
      </div>
      <div className="p-5 sm:p-6">
        <Link
          href="/dashboard/ai-modules"
          className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to AI Audit Modules
        </Link>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-5">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/30">
            <Receipt className="h-7 w-7" strokeWidth={1.75} aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">
                {MODULE_TITLE}
              </h1>
              <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-indigo-800 ring-1 ring-indigo-200 dark:bg-indigo-950/60 dark:text-indigo-300 dark:ring-indigo-800">
                Enterprise
              </span>
              <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-800">
                Active
              </span>
            </div>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              {MODULE_DESCRIPTION}
            </p>
            <div className="mt-3 inline-flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
              Modules #13 Customer Balance · #20 Invoice Checking · #4 GST Mismatch
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
