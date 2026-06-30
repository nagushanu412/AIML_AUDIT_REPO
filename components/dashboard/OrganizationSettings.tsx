"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createOrganization,
  fetchMyOrganization,
  updateMyOrganization,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { ApiOrganization } from "@/lib/api/types";

export function OrganizationSettings() {
  const [organization, setOrganization] = useState<ApiOrganization | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [createName, setCreateName] = useState("");
  const [editName, setEditName] = useState("");
  const [editSlug, setEditSlug] = useState("");

  const loadOrganization = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const org = await fetchMyOrganization();
      setOrganization(org);
      setEditName(org.name);
      setEditSlug(org.slug);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setOrganization(null);
      } else {
        setError(err instanceof Error ? err.message : "Failed to load organization");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const org = await createOrganization({ name: createName.trim() });
      setOrganization(org);
      setEditName(org.name);
      setEditSlug(org.slug);
      setCreateName("");
      setSuccess("Audit firm organization created successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create organization");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(event: React.FormEvent) {
    event.preventDefault();
    if (!organization) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const org = await updateMyOrganization({
        name: editName.trim(),
        slug: editSlug.trim(),
      });
      setOrganization(org);
      setEditName(org.name);
      setEditSlug(org.slug);
      setSuccess("Organization profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update organization");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading organization…</p>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {success}
        </p>
      )}

      {!organization ? (
        <div className="max-w-lg rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-900">Create audit firm</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Register your CA / audit firm as an organization on the platform.
            </p>
          </div>
          <form onSubmit={handleCreate} className="space-y-4 px-5 py-4">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Firm name</span>
              <input
                type="text"
                required
                minLength={2}
                maxLength={255}
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="ABC & Co Chartered Accountants"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <button
              type="submit"
              disabled={saving || createName.trim().length < 2}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Creating…" : "Create organization"}
            </button>
          </form>
        </div>
      ) : (
        <div className="max-w-lg rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-900">Audit firm organization</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Your firm profile on AIML Audit
            </p>
          </div>
          <form onSubmit={handleUpdate} className="space-y-4 px-5 py-4">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Firm name</span>
              <input
                type="text"
                required
                minLength={2}
                maxLength={255}
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Slug</span>
              <input
                type="text"
                required
                pattern="[a-z0-9]+(-[a-z0-9]+)*"
                value={editSlug}
                onChange={(e) => setEditSlug(e.target.value.toLowerCase())}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              />
            </label>
            <dl className="grid grid-cols-2 gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm">
              <dt className="text-slate-500">Status</dt>
              <dd className="font-medium capitalize text-slate-900">{organization.status}</dd>
              <dt className="text-slate-500">Organization ID</dt>
              <dd className="truncate font-mono text-xs text-slate-700">{organization.id}</dd>
            </dl>
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
