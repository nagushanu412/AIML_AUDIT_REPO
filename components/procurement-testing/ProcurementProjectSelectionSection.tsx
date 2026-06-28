"use client";

import Link from "next/link";
import { FolderKanban } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type { ApiProject } from "@/lib/api/types";

interface ProcurementProjectSelectionSectionProps {
  projects: ApiProject[];
  selectedProjectId: string;
  onProjectChange: (projectId: string) => void;
  disabled?: boolean;
}

export function ProcurementProjectSelectionSection({
  projects,
  selectedProjectId,
  onProjectChange,
  disabled = false,
}: ProcurementProjectSelectionSectionProps) {
  const selected = projects.find((p) => p.id === selectedProjectId);

  return (
    <SectionCard
      title="Procurement Testing Project"
      description="Select a Procurement Testing Project for this engagement. Only procurement_testing projects appear here."
      className="border-teal-100/80 dark:border-teal-900/30"
    >
      <div className="space-y-1.5">
        <label
          htmlFor="select-procurement-project"
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Procurement Testing Project
        </label>
        <select
          id="select-procurement-project"
          value={selectedProjectId}
          onChange={(e) => onProjectChange(e.target.value)}
          disabled={disabled || !projects.length}
          className="block w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/30 disabled:cursor-not-allowed disabled:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
        >
          <option value="">— Select procurement project —</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {!disabled && !projects.length && (
        <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          No Procurement Testing Project for this engagement. Create one under{" "}
          <Link href="/dashboard/projects" className="font-medium underline">
            Audit Projects
          </Link>{" "}
          with type <strong>Procurement testing</strong>.
        </p>
      )}

      {selected && (
        <div className="mt-4 flex gap-3 rounded-lg border border-teal-100 bg-teal-50/50 p-4 dark:border-teal-900/50 dark:bg-teal-950/30">
          <FolderKanban className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" />
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Active procurement project
            </p>
            <p className="mt-0.5 text-sm font-medium text-slate-900 dark:text-white">
              {selected.name}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              {selected.total_entries} invoices · {selected.status} · Modules #5 + #6 + #7
            </p>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
