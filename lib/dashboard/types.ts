import type { LucideIcon } from "lucide-react";

export type ModuleStatus = "active" | "coming_soon";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface DashboardStat {
  id: string;
  label: string;
  value: number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon: LucideIcon;
}

export interface RecentActivity {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  type: "engagement" | "document" | "finding" | "client" | "module";
}

export interface AuditModule {
  id: string;
  name: string;
  description: string;
  status: ModuleStatus;
  slug: string;
  icon: LucideIcon;
  category: string;
}
