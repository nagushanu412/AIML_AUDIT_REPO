import { Sparkles } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { COMING_SOON_FEATURES } from "@/lib/journal-entry-testing/constants";

export function ComingSoonFeatures() {
  return (
    <SectionCard
      title="Coming Soon — Enterprise Features"
      description="Advanced capabilities planned for the AIML Audit platform."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {COMING_SOON_FEATURES.map((feature) => (
          <article
            key={feature.id}
            className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-4 dark:border-slate-600 dark:bg-slate-800/30"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-200/80 text-slate-500 dark:bg-slate-700 dark:text-slate-400">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    {feature.title}
                  </h3>
                  <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                    Soon
                  </span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                  {feature.description}
                </p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </SectionCard>
  );
}
