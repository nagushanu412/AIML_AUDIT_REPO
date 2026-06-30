"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  assignEngagementTeamMember,
  fetchEngagementTeam,
  fetchEngagementTeamHistory,
  fetchEngagementTeamSummary,
  fetchOrganizationMembers,
  removeEngagementTeamMember,
  updateEngagementTeamMember,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type {
  ApiEngagementTeamHistory,
  ApiEngagementTeamMember,
  ApiOrganizationMember,
} from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/Button";

const MANAGER_ROLES = new Set(["organization_owner", "audit_manager", "partner"]);

const TEAM_ROLES = [
  { value: "partner", label: "Engagement Partner" },
  { value: "audit_manager", label: "Audit Manager" },
  { value: "senior_auditor", label: "Senior Auditor" },
  { value: "auditor", label: "Auditor" },
  { value: "reviewer", label: "Reviewer" },
] as const;

function roleLabel(role: string): string {
  return TEAM_ROLES.find((r) => r.value === role)?.label ?? role;
}

function actionLabel(action: string): string {
  switch (action) {
    case "assigned":
      return "Assigned";
    case "role_changed":
      return "Role changed";
    case "removed":
      return "Removed";
    case "reactivated":
      return "Reactivated";
    default:
      return action;
  }
}

interface EngagementTeamPanelProps {
  engagementId: string;
}

export function EngagementTeamPanel({ engagementId }: EngagementTeamPanelProps) {
  const { session } = useAuth();
  const canManage = MANAGER_ROLES.has(session?.user.memberRole ?? "");

  const [members, setMembers] = useState<ApiEngagementTeamMember[]>([]);
  const [total, setTotal] = useState(0);
  const [orgMembers, setOrgMembers] = useState<ApiOrganizationMember[]>([]);
  const [history, setHistory] = useState<ApiEngagementTeamHistory[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [partnerName, setPartnerName] = useState<string | null>(null);
  const [managerName, setManagerName] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [showHistory, setShowHistory] = useState(false);
  const [roleFilter, setRoleFilter] = useState("");
  const [search, setSearch] = useState("");

  const [assignUserId, setAssignUserId] = useState("");
  const [assignRole, setAssignRole] = useState("auditor");
  const [assignNotes, setAssignNotes] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [teamResult, summary, orgList] = await Promise.all([
        fetchEngagementTeam(engagementId, {
          status: "active",
          role: roleFilter || undefined,
          search: search.trim() || undefined,
          limit: 50,
        }),
        fetchEngagementTeamSummary(engagementId),
        fetchOrganizationMembers().catch(() => [] as ApiOrganizationMember[]),
      ]);
      setMembers(teamResult.items);
      setTotal(teamResult.total);
      setOrgMembers(orgList.filter((m) => m.status === "active" || m.status === "invited"));
      setPartnerName(summary.partner?.full_name ?? null);
      setManagerName(summary.audit_manager?.full_name ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load engagement team");
    } finally {
      setLoading(false);
    }
  }, [engagementId, roleFilter, search]);

  const loadHistory = useCallback(async () => {
    try {
      const result = await fetchEngagementTeamHistory(engagementId, { limit: 25 });
      setHistory(result.items);
      setHistoryTotal(result.total);
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 403)) {
        setError(err instanceof Error ? err.message : "Failed to load assignment history");
      }
    }
  }, [engagementId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (showHistory) {
      loadHistory();
    }
  }, [showHistory, loadHistory]);

  const assignedUserIds = new Set(members.map((m) => m.user_id));
  const availableOrgMembers = orgMembers.filter(
    (m) =>
      !assignedUserIds.has(m.user_id) &&
      m.role !== "client_user" &&
      m.role !== "read_only"
  );

  async function handleAssign(e: FormEvent) {
    e.preventDefault();
    if (!assignUserId) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await assignEngagementTeamMember(engagementId, {
        user_id: assignUserId,
        role: assignRole,
        notes: assignNotes.trim() || undefined,
      });
      setAssignUserId("");
      setAssignNotes("");
      setAssignRole("auditor");
      setSuccess("Team member assigned.");
      await load();
      if (showHistory) await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign team member");
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(memberId: string, role: string) {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await updateEngagementTeamMember(engagementId, memberId, { role });
      setSuccess("Role updated.");
      await load();
      if (showHistory) await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update role");
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove(member: ApiEngagementTeamMember) {
    if (!window.confirm(`Remove ${member.full_name} from this engagement team?`)) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await removeEngagementTeamMember(engagementId, member.id);
      setSuccess(`${member.full_name} removed from team.`);
      await load();
      if (showHistory) await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove team member");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-6 text-sm text-slate-500">
        Loading engagement team…
      </div>
    );
  }

  return (
    <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-4 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Engagement Team</h3>
          <p className="mt-0.5 text-xs text-slate-500">
            {total} active member{total === 1 ? "" : "s"}
            {partnerName ? ` · Partner: ${partnerName}` : " · No partner assigned"}
            {managerName ? ` · Manager: ${managerName}` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowHistory((v) => !v)}
          className="text-xs font-medium text-brand-600 hover:text-brand-700"
        >
          {showHistory ? "Hide history" : "Assignment history"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          placeholder="Search by name or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
        >
          <option value="">All roles</option>
          {TEAM_ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </div>

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

      {canManage && (
        <form
          onSubmit={handleAssign}
          className="grid gap-2 rounded-lg border border-slate-200 bg-white p-3 sm:grid-cols-4"
        >
          <select
            value={assignUserId}
            onChange={(e) => setAssignUserId(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs sm:col-span-2"
            required
          >
            <option value="">— Select organization member —</option>
            {availableOrgMembers.map((m) => (
              <option key={m.id} value={m.user_id}>
                {m.full_name || m.email} ({m.role.replace(/_/g, " ")})
              </option>
            ))}
          </select>
          <select
            value={assignRole}
            onChange={(e) => setAssignRole(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs"
          >
            {TEAM_ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          <Button type="submit" variant="primary" size="sm" isLoading={saving}>
            Assign
          </Button>
          <input
            type="text"
            placeholder="Notes (optional)"
            value={assignNotes}
            onChange={(e) => setAssignNotes(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs sm:col-span-4"
          />
        </form>
      )}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Name</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Email</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Role</th>
              <th className="px-3 py-2 text-left font-medium text-slate-600">Assigned</th>
              {canManage && (
                <th className="px-3 py-2 text-right font-medium text-slate-600">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {members.length === 0 ? (
              <tr>
                <td
                  colSpan={canManage ? 5 : 4}
                  className="px-3 py-4 text-center text-slate-500"
                >
                  No team members assigned yet.
                </td>
              </tr>
            ) : (
              members.map((member) => (
                <tr key={member.id} className="hover:bg-slate-50/80">
                  <td className="px-3 py-2 font-medium text-slate-900">{member.full_name}</td>
                  <td className="px-3 py-2 text-slate-600">{member.email}</td>
                  <td className="px-3 py-2">
                    {canManage ? (
                      <select
                        value={member.role}
                        disabled={saving}
                        onChange={(e) => handleRoleChange(member.id, e.target.value)}
                        className="rounded border border-slate-200 px-2 py-1 text-xs"
                      >
                        {TEAM_ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="capitalize text-slate-700">{roleLabel(member.role)}</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {new Date(member.assigned_at).toLocaleDateString()}
                    {member.assigned_by_name ? ` · ${member.assigned_by_name}` : ""}
                  </td>
                  {canManage && (
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        disabled={saving}
                        onClick={() => handleRemove(member)}
                        className="rounded px-2 py-1 text-red-600 hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showHistory && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Assignment History ({historyTotal})
          </h4>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">When</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">User</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Action</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Role</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                      No assignment history yet.
                    </td>
                  </tr>
                ) : (
                  history.map((entry) => (
                    <tr key={entry.id}>
                      <td className="px-3 py-2 text-slate-500">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-slate-700">{entry.user_full_name}</td>
                      <td className="px-3 py-2 text-slate-700">{actionLabel(entry.action)}</td>
                      <td className="px-3 py-2 text-slate-700">
                        {roleLabel(entry.role)}
                        {entry.previous_role
                          ? ` (was ${roleLabel(entry.previous_role)})`
                          : ""}
                      </td>
                      <td className="px-3 py-2 text-slate-500">
                        {entry.changed_by_name ?? "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
