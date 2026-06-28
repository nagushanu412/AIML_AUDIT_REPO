import { ClipboardCheck, Copy, FileCheck2, Receipt } from "lucide-react";
import { ENTERPRISE_MODULES } from "@/lib/procurement-testing/constants";

const ICONS = {
  "po-matching": ClipboardCheck,
  "vendor-invoice": Receipt,
  "duplicate-payment": Copy,
  "gst-itc": FileCheck2,
} as const;

export function EnterpriseCapabilitiesPanel() {
  return (
    <section className="rounded-xl border border-teal-100 bg-gradient-to-r from-teal-50/50 to-emerald-50/30 p-5 dark:border-teal-900/40 dark:from-teal-950/20 dark:to-emerald-950/10">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-teal-800 dark:text-teal-300">
        Enterprise AI Modules in this Workstream
      </h2>
      <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
        Procurement testing orchestrates multiple audit modules in a single enterprise workflow.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ENTERPRISE_MODULES.map((mod) => {
          const Icon = ICONS[mod.id as keyof typeof ICONS] ?? Receipt;
          return (
            <article
              key={mod.id}
              className="rounded-lg border border-white/80 bg-white/90 p-3 shadow-sm dark:border-slate-700 dark:bg-slate-900/80"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600">
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
