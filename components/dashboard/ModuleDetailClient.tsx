"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { fetchModuleCatalog } from "@/lib/api";
import { mapCatalogList } from "@/lib/dashboard/catalogUtils";
import { AUDIT_MODULES } from "@/lib/dashboard/modules";
import type { AuditModule } from "@/lib/dashboard/types";

interface ModuleDetailClientProps {
  slug: string;
}

export function ModuleDetailClient({ slug }: ModuleDetailClientProps) {
  const [module, setModule] = useState<AuditModule | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const catalog = await fetchModuleCatalog();
        if (cancelled) return;
        const mapped = mapCatalogList(catalog);
        const found = mapped.find((m) => m.slug === slug);
        if (found && found.status === "active") {
          setModule(found);
        } else {
          setNotFound(true);
        }
      } catch {
        if (cancelled) return;
        const fallback = AUDIT_MODULES.find((m) => m.slug === slug);
        if (fallback && fallback.status === "active") {
          setModule(fallback);
        } else {
          setNotFound(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <DashboardShell title="Loading…" subtitle="AI Audit Modules">
        <p className="text-sm text-slate-500">Loading module…</p>
      </DashboardShell>
    );
  }

  if (notFound || !module) {
    return (
      <DashboardShell title="Module not found" subtitle="AI Audit Modules">
        <Link
          href="/dashboard/ai-modules"
          className="text-sm font-medium text-brand-600 hover:text-brand-500"
        >
          ← Back to catalog
        </Link>
      </DashboardShell>
    );
  }

  const Icon = module.icon;

  return (
    <DashboardShell title={module.name} subtitle={module.category}>
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
              <p className="mt-3 text-slate-600">{module.description}</p>
            </div>
          </div>

          <div className="mt-8 rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
            <p className="text-sm font-medium text-slate-700">Module workspace</p>
            <p className="mt-1 text-sm text-slate-500">
              Connect your engagement data to run {module.name.toLowerCase()} procedures.
            </p>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
