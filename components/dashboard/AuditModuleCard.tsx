import Link from "next/link";
import { ArrowRight, Clock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { moduleOpenHref } from "@/lib/dashboard/catalogUtils";
import type { AuditModule } from "@/lib/dashboard/types";
import { cn } from "@/lib/utils/cn";

interface AuditModuleCardProps {
  module: AuditModule;
}

export function AuditModuleCard({ module }: AuditModuleCardProps) {
  const Icon = module.icon;
  const isActive = module.status === "active";

  return (
    <article
      className={cn(
        "flex flex-col rounded-xl border bg-white p-5 shadow-sm transition-all",
        isActive
          ? "border-slate-200/80 hover:border-brand-200 hover:shadow-md"
          : "border-slate-200/60 opacity-95"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ring-1",
            isActive
              ? "bg-brand-50 text-brand-600 ring-brand-100"
              : "bg-slate-100 text-slate-500 ring-slate-200"
          )}
        >
          <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden="true" />
        </div>

        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ring-1",
            isActive
              ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
              : "bg-slate-100 text-slate-600 ring-slate-200"
          )}
        >
          {!isActive && <Clock className="h-3 w-3" aria-hidden="true" />}
          {isActive ? "Active" : "Coming Soon"}
        </span>
      </div>

      <div className="mt-4 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {module.category}
        </p>
        <h3 className="mt-1 font-display text-base font-semibold text-slate-900">
          {module.name}
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          {module.description}
        </p>
      </div>

      <div className="mt-5">
        {isActive ? (
          <Link href={moduleOpenHref(module)}>
            <Button variant="primary" size="sm" fullWidth>
              Open Module
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </Link>
        ) : (
          <Button variant="secondary" size="sm" fullWidth disabled>
            Coming Soon
          </Button>
        )}
      </div>
    </article>
  );
}
