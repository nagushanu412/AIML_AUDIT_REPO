import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";

interface PlaceholderPageProps {
  title: string;
  subtitle: string;
}

export function DashboardPlaceholderPage({ title, subtitle }: PlaceholderPageProps) {
  return (
    <DashboardShell title={title} subtitle={subtitle}>
      <div className="flex min-h-[320px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white">
        <div className="text-center">
          <p className="font-display text-lg font-semibold text-slate-900">{title}</p>
          <p className="mt-2 text-sm text-slate-500">This section is under development.</p>
        </div>
      </div>
    </DashboardShell>
  );
}

export function createPlaceholderMetadata(title: string): Metadata {
  return {
    title: `${title} | AIML Audit`,
  };
}
