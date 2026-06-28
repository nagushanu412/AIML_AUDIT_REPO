import { FileSearch, Receipt, Scale, Users } from "lucide-react";
import { ENTERPRISE_MODULES } from "@/lib/revenue-testing/constants";

const ICONS = {
  "invoice-checking": Receipt,
  "customer-balance": Users,
  "gst-mismatch": Scale,
  "ledger-scrutiny": FileSearch,
} as const;

export function EnterpriseCapabilitiesPanel() {
  return (
    <section className="rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/50 to-violet-50/30 p-5 dark:border-indigo-900/40 dark:from-indigo-950/20 dark:to-violet-950/10">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-300">
        Enterprise AI Modules in this Workstream
      </h2>
      <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
        Revenue testing orchestrates multiple audit modules in a single enterprise workflow.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ENTERPRISE_MODULES.map((mod) => {
          const Icon = ICONS[mod.id as keyof typeof ICONS];
          return (
            <article
              key={mod.id}
              className="rounded-lg border border-white/80 bg-white/90 p-3 shadow-sm dark:border-slate-700 dark:bg-slate-900/80"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                  {mod.number}
                </span>
              </div>
              <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">
                {mod.title}
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                {mod.description}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
