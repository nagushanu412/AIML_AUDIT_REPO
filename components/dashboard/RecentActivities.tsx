import {
  AlertTriangle,
  Briefcase,
  Bot,
  FileText,
  Users,
} from "lucide-react";
import { RECENT_ACTIVITIES } from "@/lib/dashboard/mockData";
import type { RecentActivity } from "@/lib/dashboard/types";
import { cn } from "@/lib/utils/cn";

const ACTIVITY_ICONS: Record<RecentActivity["type"], typeof Bot> = {
  engagement: Briefcase,
  document: FileText,
  finding: AlertTriangle,
  client: Users,
  module: Bot,
};

const ACTIVITY_COLORS: Record<RecentActivity["type"], string> = {
  engagement: "bg-blue-50 text-blue-600 ring-blue-100",
  document: "bg-slate-100 text-slate-600 ring-slate-200",
  finding: "bg-amber-50 text-amber-600 ring-amber-100",
  client: "bg-emerald-50 text-emerald-600 ring-emerald-100",
  module: "bg-brand-50 text-brand-600 ring-brand-100",
};

export function RecentActivities() {
  return (
    <section
      className="rounded-xl border border-slate-200/80 bg-white shadow-sm"
      aria-labelledby="recent-activities-heading"
    >
      <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
        <h2
          id="recent-activities-heading"
          className="font-display text-base font-semibold text-slate-900"
        >
          Recent Activities
        </h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Latest updates across engagements, documents, and AI modules
        </p>
      </div>

      <ul className="divide-y divide-slate-100" role="list">
        {RECENT_ACTIVITIES.map((activity) => {
          const Icon = ACTIVITY_ICONS[activity.type];

          return (
            <li
              key={activity.id}
              className="flex gap-4 px-5 py-4 transition-colors hover:bg-slate-50/80 sm:px-6"
            >
              <div
                className={cn(
                  "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ring-1",
                  ACTIVITY_COLORS[activity.type]
                )}
              >
                <Icon className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">{activity.title}</p>
                <p className="mt-0.5 truncate text-sm text-slate-500">
                  {activity.description}
                </p>
              </div>
              <time className="shrink-0 text-xs text-slate-400">{activity.timestamp}</time>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
