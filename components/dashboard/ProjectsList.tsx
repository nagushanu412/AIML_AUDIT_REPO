"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Pencil, Trash2 } from "lucide-react";
import {
  createProject,
  deleteProject,
  fetchClients,
  fetchEngagements,
  fetchProjects,
  updateProject,
} from "@/lib/api";
import type { ApiProject } from "@/lib/api/types";

export function ProjectsList() {
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [engagementLabels, setEngagementLabels] = useState<Record<string, string>>({});
  const [engagementOptions, setEngagementOptions] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [engagementId, setEngagementId] = useState("");
  const [name, setName] = useState("");
  const [projectType, setProjectType] = useState("journal_testing");
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [status, setStatus] = useState("active");

  const load = () => {
    Promise.all([fetchProjects(), fetchClients(), fetchEngagements()])
      .then(([projectRows, clients, engagements]) => {
        setProjects(projectRows);
        const clientMap = Object.fromEntries(clients.map((c) => [c.id, c.name]));
        const labels = Object.fromEntries(
          engagements.map((e) => [
            e.id,
            `${clientMap[e.client_id] ?? "Client"} — ${e.financial_year}`,
          ])
        );
        setEngagementLabels(labels);
        setEngagementOptions(
          engagements.map((e) => ({
            id: e.id,
            label: labels[e.id],
          }))
        );
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load projects")
      );
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        await updateProject(editingId, { name: name.trim(), status });
      } else {
        if (!engagementId) return;
        await createProject({
          engagement_id: engagementId,
          name: name.trim(),
          project_type: projectType,
        });
      }
      setName("");
      setEditingId(null);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save project");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this project and all uploaded data?")) return;
    try {
      await deleteProject(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button type="button" variant="primary" size="sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "Add Project"}
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700">Engagement</label>
            <select
              value={engagementId}
              onChange={(e) => setEngagementId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              required
            >
              <option value="">— Select engagement —</option>
              {engagementOptions.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Journal Testing"
            required
          />
          <div>
            <label className="block text-sm font-medium text-slate-700">Type</label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            >
              <option value="journal_testing">Journal Testing</option>
              <option value="revenue_testing">Revenue Testing</option>
              <option value="procurement_testing">Procurement Testing</option>
            </select>
          </div>
          {editingId && (
            <div>
              <label className="block text-sm font-medium text-slate-700">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          )}
          <Button type="submit" variant="primary" size="sm" isLoading={saving}>
            {editingId ? "Update" : "Create"} Project
          </Button>
        </form>
      )}

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Project</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Engagement</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Entries</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {projects.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50/80">
                <td className="px-4 py-3 font-medium text-slate-900">{p.name}</td>
                <td className="px-4 py-3 text-slate-600">
                  {engagementLabels[p.engagement_id] ?? p.engagement_id.slice(0, 8)}
                </td>
                <td className="px-4 py-3 text-slate-600">{p.project_type}</td>
                <td className="px-4 py-3 text-slate-600">{p.total_entries}</td>
                <td className="px-4 py-3 capitalize text-slate-600">{p.status}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(p.id);
                        setName(p.name);
                        setStatus(p.status);
                        setShowForm(true);
                      }}
                      className="rounded p-1.5 text-slate-500 hover:bg-slate-100"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(p.id)}
                      className="rounded p-1.5 text-red-500 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
