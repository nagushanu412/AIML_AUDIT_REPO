"use client";

import { FolderKanban } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type { ApiProject } from "@/lib/api/types";

interface ProjectSelectionSectionProps {
  projects: ApiProject[];
  selectedProjectId: string;
  onProjectChange: (projectId: string) => void;
  disabled?: boolean;
}

export function ProjectSelectionSection({
  projects,
  selectedProjectId,
  onProjectChange,
  disabled = false,
}: ProjectSelectionSectionProps) {
  const selected = projects.find((p) => p.id === selectedProjectId);

  return (
    <SectionCard
      title="Audit Project"
      description="Select the audit project where journal entries will be uploaded and analyzed."
    >
      <div className="space-y-1.5">
        <label
          htmlFor="select-project"
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Select Project
        </label>
        <select
          id="select-project"
          value={selectedProjectId}
          onChange={(e) => onProjectChange(e.target.value)}
          disabled={disabled || !projects.length}
          className="block w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:cursor-not-allowed disabled:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
        >
          <option value="">— Select project —</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.project_type.replace(/_/g, " ")})
            </option>
          ))}
        </select>
      </div>

      {selected && (
        <div className="mt-4 flex gap-3 rounded-lg border border-brand-100 bg-brand-50/50 p-4 dark:border-brand-900/50 dark:bg-brand-950/30">
          <FolderKanban className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Active project
            </p>
            <p className="mt-0.5 text-sm font-medium text-slate-900 dark:text-white">
              {selected.name}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              {selected.total_entries} entries · {selected.status}
            </p>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
