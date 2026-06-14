"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Pencil, Trash2 } from "lucide-react";
import {
  createEngagement,
  deleteEngagement,
  fetchClients,
  fetchEngagements,
  updateEngagement,
} from "@/lib/api";
import type { ApiEngagement } from "@/lib/api/types";

export function EngagementsList() {
  const [engagements, setEngagements] = useState<ApiEngagement[]>([]);
  const [clientNames, setClientNames] = useState<Record<string, string>>({});
  const [clientOptions, setClientOptions] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [clientId, setClientId] = useState("");
  const [financialYear, setFinancialYear] = useState("FY 2026-27");
  const [fyEnd, setFyEnd] = useState("2027-03-31");
  const [largeValueThreshold, setLargeValueThreshold] = useState("100000");
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [status, setStatus] = useState("active");

  const load = () => {
    Promise.all([fetchClients(), fetchEngagements()])
      .then(([clients, rows]) => {
        setClientNames(Object.fromEntries(clients.map((c) => [c.id, c.name])));
        setClientOptions(clients.map((c) => ({ id: c.id, name: c.name })));
        setEngagements(rows);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load engagements")
      );
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setEditingId(null);
    setShowForm(false);
    setFinancialYear("FY 2026-27");
    setFyEnd("2027-03-31");
    setLargeValueThreshold("100000");
    setStatus("active");
    setClientId("");
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!financialYear.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const threshold = Number(largeValueThreshold);
      if (editingId) {
        await updateEngagement(editingId, {
          financial_year: financialYear.trim(),
          status,
          financial_year_end: fyEnd,
          large_value_threshold: threshold,
        });
      } else {
        if (!clientId || !fyEnd) return;
        await createEngagement({
          client_id: clientId,
          financial_year: financialYear.trim(),
          financial_year_end: fyEnd,
          audit_type: "Statutory",
          large_value_threshold: threshold,
        });
      }
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save engagement");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this engagement and all projects?")) return;
    try {
      await deleteEngagement(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          type="button"
          variant="primary"
          size="sm"
          onClick={() => {
            if (showForm) resetForm();
            else setShowForm(true);
          }}
        >
          {showForm ? "Cancel" : "Add Engagement"}
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          {!editingId && (
            <div>
              <label className="block text-sm font-medium text-slate-700">Client</label>
              <select
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                required
              >
                <option value="">— Select client —</option>
                {clientOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <Input
            label="Financial year"
            value={financialYear}
            onChange={(e) => setFinancialYear(e.target.value)}
            placeholder="FY 2026-27"
            required
          />
          <Input
            label="Financial year end"
            type="date"
            value={fyEnd}
            onChange={(e) => setFyEnd(e.target.value)}
            required
          />
          <Input
            label="Large value threshold (₹)"
            type="number"
            min={1}
            value={largeValueThreshold}
            onChange={(e) => setLargeValueThreshold(e.target.value)}
            hint="Default for LARGE_VALUE rule unless overridden in Audit Rules"
            required
          />
          {editingId && (
            <div>
              <label className="block text-sm font-medium text-slate-700">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                <option value="active">Active</option>
                <option value="planned">Planned</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          )}
          <Button type="submit" variant="primary" size="sm" isLoading={saving}>
            {editingId ? "Update" : "Create"} Engagement
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
              <th className="px-4 py-3 text-left font-medium text-slate-600">Client</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Financial Year</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Large Value (₹)</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {engagements.map((eng) => (
              <tr key={eng.id} className="hover:bg-slate-50/80">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {clientNames[eng.client_id] ?? eng.client_id}
                </td>
                <td className="px-4 py-3 text-slate-600">{eng.financial_year}</td>
                <td className="px-4 py-3 text-slate-600">{eng.audit_type}</td>
                <td className="px-4 py-3 text-slate-600">
                  {Number(eng.large_value_threshold).toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-3 capitalize text-slate-600">{eng.status}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(eng.id);
                        setFinancialYear(eng.financial_year);
                        setFyEnd(eng.financial_year_end);
                        setLargeValueThreshold(String(eng.large_value_threshold));
                        setStatus(eng.status);
                        setShowForm(true);
                      }}
                      className="rounded p-1.5 text-slate-500 hover:bg-slate-100"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(eng.id)}
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
