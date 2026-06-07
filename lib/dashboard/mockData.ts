import {
  AlertTriangle,
  Briefcase,
  FileText,
  FolderOpen,
  Users,
} from "lucide-react";
import type { DashboardStat, RecentActivity } from "./types";

export const DASHBOARD_STATS: DashboardStat[] = [
  {
    id: "clients",
    label: "Total Clients",
    value: 48,
    change: "+3 this month",
    trend: "up",
    icon: Users,
  },
  {
    id: "engagements",
    label: "Total Audit Engagements",
    value: 127,
    change: "12 in progress",
    trend: "neutral",
    icon: Briefcase,
  },
  {
    id: "documents",
    label: "Total Documents",
    value: 3842,
    change: "+218 this week",
    trend: "up",
    icon: FolderOpen,
  },
  {
    id: "findings",
    label: "AI Findings",
    value: 156,
    change: "23 require review",
    trend: "down",
    icon: AlertTriangle,
  },
];

export const RECENT_ACTIVITIES: RecentActivity[] = [
  {
    id: "act-1",
    title: "Journal Entry Testing completed",
    description: "FY24 statutory audit — Apex Manufacturing Pvt. Ltd.",
    timestamp: "12 minutes ago",
    type: "module",
  },
  {
    id: "act-2",
    title: "New engagement created",
    description: "Internal audit — Greenfield Logistics LLP (Q1 FY25)",
    timestamp: "45 minutes ago",
    type: "engagement",
  },
  {
    id: "act-3",
    title: "AI finding flagged",
    description: "Duplicate payment detected — Vendor INV-8842 (₹1,24,500)",
    timestamp: "1 hour ago",
    type: "finding",
  },
  {
    id: "act-4",
    title: "Documents uploaded",
    description: "142 trial balance schedules — Sunrise Retail Chain",
    timestamp: "2 hours ago",
    type: "document",
  },
  {
    id: "act-5",
    title: "Client onboarded",
    description: "Horizon Tech Solutions — Enterprise tier",
    timestamp: "3 hours ago",
    type: "client",
  },
  {
    id: "act-6",
    title: "Ledger Scrutiny in progress",
    description: "Materiality threshold review — Pinnacle Finance Co.",
    timestamp: "5 hours ago",
    type: "module",
  },
  {
    id: "act-7",
    title: "Working papers exported",
    description: "GST audit module — Coastal Exports India",
    timestamp: "Yesterday",
    type: "document",
  },
  {
    id: "act-8",
    title: "Engagement status updated",
    description: "Fieldwork phase — Metro Healthcare Associates",
    timestamp: "Yesterday",
    type: "engagement",
  },
];
