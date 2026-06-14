"use client";

import { useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import type { ApiUserProfile } from "@/lib/api/types";

export function SettingsProfile() {
  const [profile, setProfile] = useState<ApiUserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profile"));
  }, []);

  if (error) {
    return (
      <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </p>
    );
  }

  if (!profile) {
    return <p className="text-sm text-slate-500">Loading profile…</p>;
  }

  const rows = [
    ["Full name", profile.full_name],
    ["Email", profile.email],
    ["Role", profile.role],
    ["Company", profile.company_name ?? "—"],
    ["Phone", profile.phone ?? "—"],
    ["Status", profile.is_active ? "Active" : "Inactive"],
  ];

  return (
    <div className="max-w-lg rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="font-semibold text-slate-900">Account profile</h2>
        <p className="mt-0.5 text-sm text-slate-500">Your auditor portal identity</p>
      </div>
      <dl className="divide-y divide-slate-100">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 px-5 py-3 text-sm">
            <dt className="text-slate-500">{label}</dt>
            <dd className="font-medium capitalize text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
