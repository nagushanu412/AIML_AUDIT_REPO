"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, X } from "lucide-react";
import { DASHBOARD_NAV } from "@/lib/dashboard/navigation";
import { DASHBOARD_PRODUCT_NAME } from "@/lib/dashboard/constants";
import { cn } from "@/lib/utils/cn";

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  const navContent = (
    <>
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500/30 ring-1 ring-white/20">
          <ShieldCheck className="h-5 w-5 text-white" strokeWidth={1.75} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-sm font-bold text-white">
            {DASHBOARD_PRODUCT_NAME}
          </p>
          <p className="truncate text-xs text-brand-200/70">Audit Platform</p>
        </div>
        <button
          type="button"
          onClick={onMobileClose}
          className="rounded-lg p-1.5 text-brand-200 hover:bg-white/10 lg:hidden"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Main">
        {DASHBOARD_NAV.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={onMobileClose}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-white/15 text-white shadow-sm ring-1 ring-white/10"
                  : "text-brand-100/80 hover:bg-white/10 hover:text-white"
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-5 w-5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-lg bg-white/5 px-3 py-3 ring-1 ring-white/10">
          <p className="text-xs font-medium text-brand-100">Enterprise Plan</p>
          <p className="mt-0.5 text-xs text-brand-200/60">14-day trial active</p>
        </div>
      </div>
    </>
  );

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-950 transition-transform duration-200 lg:static lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Sidebar navigation"
      >
        {navContent}
      </aside>
    </>
  );
}
