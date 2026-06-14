import {
  Bot,
  Briefcase,
  FileText,
  LayoutDashboard,
  Settings,
  Users,
  BarChart3,
  FolderOpen,
  Scale,
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
    id: "projects",
    label: "Audit Projects",
    href: "/dashboard/projects",
    icon: FileText,
  },
  {
    id: "documents",
    label: "Documents",
    href: "/dashboard/documents",
    icon: FolderOpen,
  },
  {
    id: "rules",
    label: "Audit Rules",
    href: "/dashboard/rules",
    icon: Scale,
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
