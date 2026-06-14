"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Clock, FolderKanban } from "lucide-react";
import { ClientEngagementSection } from "@/components/journal-entry-testing/ClientEngagementSection";
import { fetchClients, fetchEngagements, fetchProjects } from "@/lib/api";
import type { ApiProject } from "@/lib/api/types";
import {
  getModulesForProjectType,
  WORKSTREAM_CONFIG,
  type WorkstreamProjectType,
} from "@/lib/dashboard/projectModuleMap";
import type { ClientOption, EngagementOption } from "@/lib/journal-entry-testing/types";

function formatEngagementPeriod(start?: string | null, end?: string | null): string {
  if (!start && !end) return "—";
  const fmt = (d: string) =>
    new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  if (start && end) return `${fmt(start)} to ${fmt(end)}`;
  return start ? fmt(start) : end ? fmt(end) : "—";
}

interface ProjectTypeWorkspaceProps {
  workstream: WorkstreamProjectType;
}

export function ProjectTypeWorkspace({ workstream }: ProjectTypeWorkspaceProps) {
  const config = WORKSTREAM_CONFIG[workstream];
  const mapping = getModulesForProjectType(workstream);

  const [clients, setClients] = useState<ClientOption[]>([]);
  const [engagements, setEngagements] = useState<EngagementOption[]>([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [selectedEngagementId, setSelectedEngagementId] = useState("");
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [projectId, setProjectId] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetchClients()
      .then((rows) => setClients(rows.map((c) => ({ id: c.id, name: c.name }))))
      .catch(() => setLoadError("Could not load clients."));
  }, []);

  useEffect(() => {
    if (!selectedClientId) {
      setEngagements([]);
      return;
    }
    fetchEngagements(selectedClientId)
      .then((rows) =>
        setEngagements(
          rows.map((e) => ({
            id: e.id,
            clientId: e.client_id,
            label: `${e.financial_year} — ${e.audit_type}`,
            auditPeriod: formatEngagementPeriod(e.start_date, e.end_date),
            financialYear: e.financial_year,
          }))
        )
      )
      .catch(() => setLoadError("Could not load engagements."));
  }, [selectedClientId]);

  useEffect(() => {
    if (!selectedEngagementId) {
      setProjects([]);
      setProjectId("");
      return;
    }
    fetchProjects(selectedEngagementId)
      .then((rows) => {
        const filtered = rows.filter((p) => p.project_type === workstream);
        setProjects(filtered);
        setProjectId(filtered[0]?.id ?? "");
      })
      .catch(() => setLoadError("Could not load projects."));
  }, [selectedEngagementId, workstream]);

  const filteredEngagements = useMemo(
    () => engagements.filter((e) => e.clientId === selectedClientId),
    [engagements, selectedClientId]
  );

  const selectedProject = projects.find((p) => p.id === projectId);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Link
        href="/dashboard/ai-modules"
        className="inline-flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to AI Audit Modules
      </Link>

      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{config.title}</h1>
        <p className="mt-1 text-sm text-slate-600">{config.subtitle}</p>
      </div>

      <p className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        {config.description}
      </p>

      {loadError && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {loadError}
        </p>
      )}

      <ClientEngagementSection
        clients={clients}
        engagements={filteredEngagements}
        selectedClientId={selectedClientId}
        selectedEngagementId={selectedEngagementId}
        onClientChange={(id) => {
          setSelectedClientId(id);
          setSelectedEngagementId("");
          setProjectId("");
          setProjects([]);
        }}
        onEngagementChange={setSelectedEngagementId}
      />

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900">{config.title} project</h2>
        <p className="mt-1 text-sm text-slate-600">
          Only {config.title.toLowerCase()} projects are shown (not journal testing).
        </p>
        <div className="mt-4 space-y-1.5">
          <label htmlFor="workstream-project" className="block text-sm font-medium text-slate-700">
            Select project
          </label>
          <select
            id="workstream-project"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            disabled={!selectedEngagementId || !projects.length}
            className="block w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm disabled:bg-slate-50"
          >
            <option value="">— Select project —</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {selectedEngagementId && !projects.length && (
          <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            No {config.title.toLowerCase()} project for this engagement. Create one under{" "}
            <Link href="/dashboard/projects" className="font-medium underline">
              Audit Projects
            </Link>{" "}
            with type <strong>{config.title}</strong>.
          </p>
        )}

        {selectedProject && (
          <div className="mt-4 flex gap-3 rounded-lg border border-brand-100 bg-brand-50/50 p-4">
            <FolderKanban className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Selected project
              </p>
              <p className="mt-0.5 text-sm font-medium text-slate-900">{selectedProject.name}</p>
              <p className="mt-0.5 text-xs text-slate-500">
                {selectedProject.total_entries} entries · {selectedProject.status}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900">Linked AI Audit Modules</h2>
        <p className="mt-1 text-sm text-slate-600">
          This workstream uses modules from the 20-module catalog (not Journal Entry Testing).
        </p>
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Primary</p>
          <ul className="mt-2 space-y-1">
            {mapping.primary.map((mod) => (
              <li key={mod} className="text-sm text-slate-800">
                {mod}
              </li>
            ))}
          </ul>
        </div>
        {mapping.supporting.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Supporting
            </p>
            <ul className="mt-2 space-y-1">
              {mapping.supporting.map((mod) => (
                <li key={mod} className="text-sm text-slate-600">
                  {mod}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6">
        <Clock className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" />
        <div>
          <p className="text-sm font-semibold text-slate-800">Upload & analysis — coming soon</p>
          <p className="mt-1 text-sm text-slate-600">
            Data upload and automated testing for {config.title.toLowerCase()} will be added in a
            future release. Use Audit Projects to plan the workstream; execution will run through
            the linked modules above.
          </p>
        </div>
      </div>
    </div>
  );
}
