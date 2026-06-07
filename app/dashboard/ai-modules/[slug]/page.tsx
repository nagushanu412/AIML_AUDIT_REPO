import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { AUDIT_MODULES } from "@/lib/dashboard/modules";

interface ModuleDetailPageProps {
  params: { slug: string };
}

export function generateStaticParams() {
  return AUDIT_MODULES.filter(
    (m) => m.status === "active" && m.slug !== "journal-entry-testing"
  ).map((m) => ({
    slug: m.slug,
  }));
}

export default function ModuleDetailPage({ params }: ModuleDetailPageProps) {
  const { slug } = params;
  const auditModule = AUDIT_MODULES.find((m) => m.slug === slug);

  if (!auditModule || auditModule.status !== "active") {
    notFound();
  }

  const Icon = auditModule.icon;

  return (
    <DashboardShell title={auditModule.name} subtitle={auditModule.category}>
      <div className="mx-auto max-w-3xl">
        <Link
          href="/dashboard/ai-modules"
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-500"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to AI Audit Modules
        </Link>

        <div className="rounded-xl border border-slate-200/80 bg-white p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100">
              <Icon className="h-7 w-7" strokeWidth={1.75} />
            </div>
            <div>
              <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
                Active
              </span>
              <p className="mt-3 text-slate-600">{auditModule.description}</p>
            </div>
          </div>

          <div className="mt-8 rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
            <p className="text-sm font-medium text-slate-700">Module workspace</p>
            <p className="mt-1 text-sm text-slate-500">
              Connect your engagement data to run {auditModule.name.toLowerCase()}{" "}
              procedures.
            </p>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
