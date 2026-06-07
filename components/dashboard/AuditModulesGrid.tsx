import { AUDIT_MODULES } from "@/lib/dashboard/modules";
import { AuditModuleCard } from "@/components/dashboard/AuditModuleCard";

export function AuditModulesGrid() {
  const activeCount = AUDIT_MODULES.filter((m) => m.status === "active").length;
  const comingSoonCount = AUDIT_MODULES.length - activeCount;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
          {activeCount} Active
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
          {comingSoonCount} Coming Soon
        </span>
        <span className="text-sm text-slate-500">
          {AUDIT_MODULES.length} audit modules available
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        {AUDIT_MODULES.map((module) => (
          <AuditModuleCard key={module.id} module={module} />
        ))}
      </div>
    </div>
  );
}
