"use client";

import { FormEvent, useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { createClient, deleteClient, fetchClients, updateClient } from "@/lib/api";
import type { ApiClient } from "@/lib/api/types";

export function ClientsList() {
  const [clients, setClients] = useState<ApiClient[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    fetchClients()
      .then(setClients)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load clients"));
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setName("");
    setIndustry("");
    setEditingId(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        await updateClient(editingId, {
          name: name.trim(),
          industry: industry.trim() || undefined,
        });
      } else {
        await createClient({
          name: name.trim(),
          industry: industry.trim() || undefined,
        });
      }
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (client: ApiClient) => {
    setEditingId(client.id);
    setName(client.name);
    setIndustry(client.industry ?? "");
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this client and all related engagements?")) return;
    setError(null);
    try {
      await deleteClient(id);
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
            resetForm();
            setShowForm(true);
          }}
        >
          Add Client
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <Input label="Client name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Industry" value={industry} onChange={(e) => setIndustry(e.target.value)} />
          <div className="flex gap-2">
            <Button type="submit" variant="primary" size="sm" isLoading={saving}>
              {editingId ? "Update" : "Create"}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={resetForm}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!clients.length ? (
        <p className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
          No clients yet. Demo data seeds ABC Manufacturing on API startup.
        </p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Client</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Industry</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-medium text-slate-900">{client.name}</td>
                  <td className="px-4 py-3 text-slate-600">{client.industry ?? "—"}</td>
                  <td className="px-4 py-3 capitalize text-slate-600">{client.status}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => startEdit(client)}
                        className="rounded p-1.5 text-slate-500 hover:bg-slate-100"
                        aria-label="Edit"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(client.id)}
                        className="rounded p-1.5 text-red-500 hover:bg-red-50"
                        aria-label="Delete"
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
      )}
    </div>
  );
}
