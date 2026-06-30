"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createWorkpaper,
  fetchEngagementEvidence,
  fetchEngagementWorkpapers,
  uploadEngagementEvidence,
  uploadWorkpaperFile,
} from "@/lib/api";
import { API_BASE_URL } from "@/lib/api/config";
import { ApiError } from "@/lib/api/client";
import type { ApiEvidence, ApiWorkpaper } from "@/lib/api/types";
import { getAccessToken } from "@/lib/auth/session";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/Button";

const MANAGE_ROLES = new Set([
  "organization_owner",
  "audit_manager",
  "partner",
  "senior_auditor",
  "auditor",
]);

const EVIDENCE_CATEGORIES = [
  { value: "invoice", label: "Invoice" },
  { value: "contract", label: "Contract" },
  { value: "correspondence", label: "Correspondence" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "screenshot", label: "Screenshot" },
  { value: "spreadsheet", label: "Spreadsheet" },
  { value: "report", label: "Report" },
  { value: "other", label: "Other" },
];

interface EngagementRepositoryPanelProps {
  engagementId: string;
}

export function EngagementRepositoryPanel({ engagementId }: EngagementRepositoryPanelProps) {
  const { session } = useAuth();
  const canManage = MANAGE_ROLES.has(session?.user.memberRole ?? "");

  const [evidence, setEvidence] = useState<ApiEvidence[]>([]);
  const [workpapers, setWorkpapers] = useState<ApiWorkpaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState<"evidence" | "workpapers">("evidence");

  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [evidenceCategory, setEvidenceCategory] = useState("other");
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);

  const [wpRef, setWpRef] = useState("");
  const [wpTitle, setWpTitle] = useState("");
  const [wpFile, setWpFile] = useState<File | null>(null);
  const [uploadWpId, setUploadWpId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ev, wp] = await Promise.all([
        fetchEngagementEvidence(engagementId, {
          search: search.trim() || undefined,
          limit: 50,
        }),
        fetchEngagementWorkpapers(engagementId, {
          search: search.trim() || undefined,
          limit: 50,
        }),
      ]);
      setEvidence(ev.items);
      setWorkpapers(wp.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repository");
    } finally {
      setLoading(false);
    }
  }, [engagementId, search]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleEvidenceUpload(e: FormEvent) {
    e.preventDefault();
    if (!evidenceFile || !evidenceTitle.trim()) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const fd = new FormData();
      fd.append("file", evidenceFile);
      fd.append("title", evidenceTitle.trim());
      fd.append("category", evidenceCategory);
      await uploadEngagementEvidence(engagementId, fd);
      setEvidenceTitle("");
      setEvidenceFile(null);
      setSuccess("Evidence uploaded.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateWorkpaper(e: FormEvent) {
    e.preventDefault();
    if (!wpRef.trim() || !wpTitle.trim()) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const wp = await createWorkpaper(engagementId, {
        reference_code: wpRef.trim(),
        title: wpTitle.trim(),
      });
      if (wpFile) {
        const fd = new FormData();
        fd.append("file", wpFile);
        await uploadWorkpaperFile(engagementId, wp.id, fd);
      }
      setWpRef("");
      setWpTitle("");
      setWpFile(null);
      setSuccess("Workpaper created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workpaper");
    } finally {
      setSaving(false);
    }
  }

  async function handleWpFileUpload(workpaperId: string, file: File) {
    setSaving(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await uploadWorkpaperFile(engagementId, workpaperId, fd);
      setUploadWpId(null);
      setSuccess("Workpaper file uploaded.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSaving(false);
    }
  }

  async function downloadFile(path: string, fileName: string) {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiError("Download failed", response.status);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-6 text-sm text-slate-500">
        Loading evidence & workpapers…
      </div>
    );
  }

  return (
    <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">Evidence & Workpapers</h3>
        <div className="flex gap-1 rounded-lg border border-slate-200 bg-white p-0.5 text-xs">
          <button
            type="button"
            onClick={() => setTab("evidence")}
            className={`rounded-md px-3 py-1 ${tab === "evidence" ? "bg-brand-50 text-brand-700" : "text-slate-600"}`}
          >
            Evidence ({evidence.length})
          </button>
          <button
            type="button"
            onClick={() => setTab("workpapers")}
            className={`rounded-md px-3 py-1 ${tab === "workpapers" ? "bg-brand-50 text-brand-700" : "text-slate-600"}`}
          >
            Workpapers ({workpapers.length})
          </button>
        </div>
      </div>

      <input
        type="search"
        placeholder="Search title, file name, reference…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-md rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
      />

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
          {success}
        </p>
      )}

      {tab === "evidence" && (
        <>
          {canManage && (
            <form
              onSubmit={handleEvidenceUpload}
              className="grid gap-2 rounded-lg border border-slate-200 bg-white p-3 sm:grid-cols-4"
            >
              <input
                type="text"
                placeholder="Evidence title"
                value={evidenceTitle}
                onChange={(e) => setEvidenceTitle(e.target.value)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs sm:col-span-2"
                required
              />
              <select
                value={evidenceCategory}
                onChange={(e) => setEvidenceCategory(e.target.value)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs"
              >
                {EVIDENCE_CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
              <input
                type="file"
                onChange={(e) => setEvidenceFile(e.target.files?.[0] ?? null)}
                className="text-xs sm:col-span-2"
                required
              />
              <Button type="submit" variant="primary" size="sm" isLoading={saving}>
                Upload Evidence
              </Button>
            </form>
          )}

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Title</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Category</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">File</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Version</th>
                  <th className="px-3 py-2 text-right font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {evidence.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                      No evidence uploaded yet.
                    </td>
                  </tr>
                ) : (
                  evidence.map((row) => (
                    <tr key={row.id}>
                      <td className="px-3 py-2 font-medium text-slate-900">{row.title}</td>
                      <td className="px-3 py-2 capitalize text-slate-600">{row.category}</td>
                      <td className="px-3 py-2 text-slate-600">{row.file_name}</td>
                      <td className="px-3 py-2 text-slate-500">v{row.version_number}</td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          className="text-brand-600 hover:underline"
                          onClick={() =>
                            downloadFile(
                              `/engagements/${engagementId}/evidence/${row.id}/download`,
                              row.file_name
                            ).catch((err) =>
                              setError(err instanceof Error ? err.message : "Download failed")
                            )
                          }
                        >
                          Download
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "workpapers" && (
        <>
          {canManage && (
            <form
              onSubmit={handleCreateWorkpaper}
              className="grid gap-2 rounded-lg border border-slate-200 bg-white p-3 sm:grid-cols-4"
            >
              <input
                type="text"
                placeholder="Reference (e.g. WP-JE-001)"
                value={wpRef}
                onChange={(e) => setWpRef(e.target.value)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs"
                required
              />
              <input
                type="text"
                placeholder="Title"
                value={wpTitle}
                onChange={(e) => setWpTitle(e.target.value)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs sm:col-span-2"
                required
              />
              <input
                type="file"
                onChange={(e) => setWpFile(e.target.files?.[0] ?? null)}
                className="text-xs sm:col-span-2"
              />
              <Button type="submit" variant="primary" size="sm" isLoading={saving}>
                Create Workpaper
              </Button>
            </form>
          )}

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Ref</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Title</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Status</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">File</th>
                  <th className="px-3 py-2 text-right font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {workpapers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                      No workpapers yet.
                    </td>
                  </tr>
                ) : (
                  workpapers.map((row) => (
                    <tr key={row.id}>
                      <td className="px-3 py-2 font-mono text-slate-800">{row.reference_code}</td>
                      <td className="px-3 py-2 text-slate-900">{row.title}</td>
                      <td className="px-3 py-2 capitalize text-slate-600">{row.status}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {row.has_file ? row.file_name : "—"}
                      </td>
                      <td className="px-3 py-2 text-right space-x-2">
                        {row.has_file && (
                          <button
                            type="button"
                            className="text-brand-600 hover:underline"
                            onClick={() =>
                              downloadFile(
                                `/engagements/${engagementId}/workpapers/${row.id}/download`,
                                row.file_name || "workpaper"
                              ).catch((err) =>
                                setError(err instanceof Error ? err.message : "Download failed")
                              )
                            }
                          >
                            Download
                          </button>
                        )}
                        {canManage && (
                          <label className="cursor-pointer text-brand-600 hover:underline">
                            {uploadWpId === row.id ? "Uploading…" : "Attach file"}
                            <input
                              type="file"
                              className="hidden"
                              disabled={saving}
                              onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) {
                                  setUploadWpId(row.id);
                                  handleWpFileUpload(row.id, f);
                                }
                              }}
                            />
                          </label>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
