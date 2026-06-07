import type { DashboardStat } from "@/lib/dashboard/types";
import { cn } from "@/lib/utils/cn";

interface StatCardProps {
  stat: DashboardStat;
}

export function StatCard({ stat }: StatCardProps) {
  const Icon = stat.icon;

  return (
    <article className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-500">{stat.label}</p>
          <p className="mt-2 font-display text-3xl font-bold tracking-tight text-slate-900">
            {stat.value.toLocaleString()}
          </p>
          {stat.change && (
            <p
              className={cn(
                "mt-2 text-xs font-medium",
                stat.trend === "up" && "text-emerald-600",
                stat.trend === "down" && "text-amber-600",
                stat.trend === "neutral" && "text-slate-500"
              )}
            >
              {stat.change}
            </p>
          )}
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100">
          <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden="true" />
        </div>
      </div>
    </article>
  );
}
