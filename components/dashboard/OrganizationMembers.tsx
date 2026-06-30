"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchOrganizationMembers,
  inviteOrganizationMember,
  removeOrganizationMember,
  updateOrganizationMember,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { ApiOrganizationMember } from "@/lib/api/types";

const INVITABLE_ROLES = [
  { value: "partner", label: "Partner" },
  { value: "audit_manager", label: "Audit Manager" },
  { value: "senior_auditor", label: "Senior Auditor" },
  { value: "auditor", label: "Auditor" },
  { value: "reviewer", label: "Reviewer" },
  { value: "client_user", label: "Client User" },
  { value: "read_only", label: "Read Only" },
] as const;

const ALL_ROLES = [
  { value: "organization_owner", label: "Organization Owner" },
  ...INVITABLE_ROLES,
];

function roleLabel(role: string): string {
  return ALL_ROLES.find((r) => r.value === role)?.label ?? role;
}

function statusBadgeClass(status: string): string {
  switch (status) {
    case "active":
      return "bg-emerald-50 text-emerald-800 border-emerald-200";
    case "invited":
      return "bg-amber-50 text-amber-800 border-amber-200";
    case "disabled":
      return "bg-slate-100 text-slate-600 border-slate-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

export function OrganizationMembers() {
  const [members, setMembers] = useState<ApiOrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("auditor");

  const [hasOrganization, setHasOrganization] = useState(true);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOrganizationMembers();
      setMembers(data);
      setCanManage(true);
      setHasOrganization(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setMembers([]);
        setHasOrganization(false);
      } else if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to view team members.");
        setMembers([]);
      } else {
        setError(err instanceof Error ? err.message : "Failed to load team members");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  async function handleInvite(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const member = await inviteOrganizationMember({
        email: inviteEmail.trim(),
        role: inviteRole,
        full_name: inviteName.trim() || undefined,
      });
      setMembers((prev) => {
        const existing = prev.find((m) => m.id === member.id);
        if (existing) {
          return prev.map((m) => (m.id === member.id ? member : m));
        }
        return [...prev, member];
      });
      setInviteEmail("");
      setInviteName("");
      setInviteRole("auditor");
      if (member.invite_email_sent) {
        setSuccess(`Invitation email sent to ${member.email}.`);
      } else if (member.invite_link) {
        setSuccess(
          `Member invited. Email is not configured — share this link with ${member.email}: ${member.invite_link}`
        );
      } else {
        setSuccess(`${member.email} was invited. They can sign in if they already have an account.`);
      }
      setCanManage(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to invite member");
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(memberId: string, role: string) {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateOrganizationMember(memberId, { role });
      setMembers((prev) => prev.map((m) => (m.id === memberId ? updated : m)));
      setSuccess("Member role updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update role");
      await loadMembers();
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove(memberId: string, email: string) {
    if (!window.confirm(`Remove ${email} from your organization?`)) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateOrganizationMember(memberId, { status: "disabled" });
      setMembers((prev) => prev.map((m) => (m.id === memberId ? updated : m)));
      setSuccess(`${email} has been removed from the organization.`);
    } catch (err) {
      try {
        const removed = await removeOrganizationMember(memberId);
        setMembers((prev) => prev.map((m) => (m.id === memberId ? removed : m)));
        setSuccess(`${email} has been removed from the organization.`);
      } catch (inner) {
        setError(
          inner instanceof Error ? inner.message : "Failed to remove member"
        );
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading team members…</p>;
  }

  if (!hasOrganization) {
    return null;
  }

  if (members.length === 0 && error && !canManage) {
    return null;
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

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="font-semibold text-slate-900">Team members</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Invite colleagues and manage roles for your audit firm.
          </p>
        </div>

        {members.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left text-slate-600">
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Email</th>
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.id} className="border-b border-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-900">
                      {member.full_name}
                    </td>
                    <td className="px-5 py-3 text-slate-600">{member.email}</td>
                    <td className="px-5 py-3">
                      {member.status === "disabled" ? (
                        <span className="text-slate-500">{roleLabel(member.role)}</span>
                      ) : (
                        <select
                          value={member.role}
                          disabled={
                            saving ||
                            member.role === "organization_owner" ||
                            member.status === "disabled"
                          }
                          onChange={(e) => handleRoleChange(member.id, e.target.value)}
                          className="rounded border border-slate-300 px-2 py-1 text-sm disabled:opacity-50"
                        >
                          {ALL_ROLES.map((r) => (
                            <option key={r.value} value={r.value}>
                              {r.label}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${statusBadgeClass(member.status)}`}
                      >
                        {member.status}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {member.status !== "disabled" &&
                        member.role !== "organization_owner" && (
                          <button
                            type="button"
                            disabled={saving}
                            onClick={() => handleRemove(member.id, member.email)}
                            className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
                          >
                            Remove
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="px-5 py-4 text-sm text-slate-500">
            No team members yet. Create an organization first, then invite colleagues.
          </p>
        )}

        <form onSubmit={handleInvite} className="space-y-4 border-t border-slate-100 px-5 py-4">
          <h3 className="text-sm font-semibold text-slate-900">Invite member</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Email</span>
              <input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@firm.com"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Full name (optional)</span>
              <input
                type="text"
                value={inviteName}
                onChange={(e) => setInviteName(e.target.value)}
                placeholder="Jane Smith"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Role</span>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {INVITABLE_ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            type="submit"
            disabled={saving || !inviteEmail.trim()}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? "Sending…" : "Send invite"}
          </button>
        </form>
      </div>
    </div>
  );
}
