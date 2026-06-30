"use client";

import { useEffect, useState } from "react";
import { Bell, LogOut, Menu, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { fetchMyOrganization } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getUserInitials } from "@/lib/auth/session";
import { cn } from "@/lib/utils/cn";

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  onMenuClick: () => void;
}

const ROLE_LABELS: Record<string, string> = {
  auditor: "Auditor",
  partner: "Partner",
  manager: "Manager",
  admin: "Administrator",
  organization_owner: "Organization Owner",
  audit_manager: "Audit Manager",
  senior_auditor: "Senior Auditor",
  reviewer: "Reviewer",
  read_only: "Read Only",
  client_user: "Client User",
};

export function DashboardHeader({
  title,
  subtitle,
  onMenuClick,
}: DashboardHeaderProps) {
  const { session, logout } = useAuth();
  const user = session?.user;
  const initials = user ? getUserInitials(user.name) : "AU";
  const [orgName, setOrgName] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.organizationId) {
      setOrgName(null);
      return;
    }
    fetchMyOrganization()
      .then((org) => setOrgName(org.name))
      .catch(() => setOrgName(null));
  }, [user?.organizationId]);

  const roleLabel =
    user?.memberRole != null
      ? (ROLE_LABELS[user.memberRole] ?? user.memberRole)
      : user
        ? (ROLE_LABELS[user.role] ?? user.role)
        : "Signed in";

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <h1 className="truncate font-display text-lg font-bold text-slate-900 sm:text-xl">
              {title}
            </h1>
            {subtitle && (
              <p className="hidden truncate text-sm text-slate-500 sm:block">
                {orgName ? `${orgName} · ${subtitle}` : subtitle}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="relative hidden md:block">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              type="search"
              placeholder="Search clients, engagements…"
              className={cn(
                "h-9 w-56 rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm",
                "placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 xl:w-72"
              )}
            />
          </div>

          <button
            type="button"
            className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
          </button>

          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white py-1 pl-1 pr-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-600 text-xs font-bold text-white">
              {initials}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-semibold text-slate-900">{user?.name ?? "Auditor"}</p>
              <p className="text-[11px] text-slate-500">{roleLabel}</p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="ml-1 hidden sm:inline-flex"
              onClick={() => logout()}
            >
              <LogOut className="h-3.5 w-3.5" />
              Logout
            </Button>
            <button
              type="button"
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 sm:hidden"
              aria-label="Logout"
              onClick={() => logout()}
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
