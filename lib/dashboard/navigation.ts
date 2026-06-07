import {
  Bot,
  Briefcase,
  FileText,
  LayoutDashboard,
  Settings,
  Users,
  BarChart3,
  FolderOpen,
} from "lucide-react";
import type { NavItem } from "./types";

export const DASHBOARD_NAV: NavItem[] = [
  { id: "dashboard", label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { id: "clients", label: "Clients", href: "/dashboard/clients", icon: Users },
  {
    id: "engagements",
    label: "Audit Engagements",
    href: "/dashboard/engagements",
    icon: Briefcase,
  },
  {
    id: "documents",
    label: "Documents",
    href: "/dashboard/documents",
    icon: FolderOpen,
  },
  {
    id: "ai-modules",
    label: "AI Audit Modules",
    href: "/dashboard/ai-modules",
    icon: Bot,
  },
  { id: "reports", label: "Reports", href: "/dashboard/reports", icon: BarChart3 },
  { id: "settings", label: "Settings", href: "/dashboard/settings", icon: Settings },
];
