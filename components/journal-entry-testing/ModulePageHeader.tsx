import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";
import { MODULE_DESCRIPTION, MODULE_TITLE } from "@/lib/journal-entry-testing/constants";

export function ModulePageHeader() {
  return (
    <div className="mb-6 rounded-xl border border-slate-200/80 bg-gradient-to-br from-white via-white to-brand-50/30 p-5 shadow-sm dark:border-slate-700/80 dark:from-slate-900 dark:via-slate-900 dark:to-brand-950/30 sm:p-6">
      <Link
        href="/dashboard/ai-modules"
        className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-500 dark:text-brand-400 dark:hover:text-brand-300"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to AI Audit Modules
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-5">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-600/25">
          <BookOpen className="h-6 w-6" strokeWidth={1.75} aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-display text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">
              {MODULE_TITLE}
            </h1>
            <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-800">
              Active Module
            </span>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            {MODULE_DESCRIPTION}
          </p>
        </div>
      </div>
    </div>
  );
}
