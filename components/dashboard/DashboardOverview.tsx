"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Briefcase, FileText, Users } from "lucide-react";
import { DashboardCharts } from "@/components/dashboard/DashboardCharts";
import { RecentActivities } from "@/components/dashboard/RecentActivities";
import { StatCard } from "@/components/dashboard/StatCard";
import { fetchDashboardSummary } from "@/lib/api";
import type { DashboardStat, RecentActivity } from "@/lib/dashboard/types";

const STAT_CONFIG: Omit<DashboardStat, "value">[] = [
  { id: "clients", label: "Active Clients", trend: "neutral", change: "Your portfolio", icon: Users },
  { id: "engagements", label: "Audit Engagements", trend: "neutral", change: "In progress", icon: Briefcase },
  { id: "entries", label: "Journal Entries", trend: "neutral", change: "Uploaded", icon: FileText },
  { id: "violations", label: "Rule Violations", trend: "neutral", change: "Flagged", icon: AlertTriangle },
];

export function DashboardOverview() {
  const [stats, setStats] = useState<DashboardStat[]>([]);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [riskDistribution, setRiskDistribution] = useState<Record<string, number>>({});
  const [violationsByRule, setViolationsByRule] = useState<Record<string, number>>({});

  useEffect(() => {
    fetchDashboardSummary()
      .then((summary) => {
        const values: Record<string, number> = {
          clients: summary.total_clients,
          engagements: summary.total_engagements,
          entries: summary.total_journal_entries,
          violations: summary.total_violations,
        };
        setStats(
          STAT_CONFIG.map((cfg) => ({
            ...cfg,
            value: values[cfg.id] ?? 0,
          }))
        );
        setRiskDistribution(summary.risk_distribution ?? {});
        setViolationsByRule(summary.violations_by_rule ?? {});
        setActivities(
          summary.recent_activities.map((a, i) => ({
            id: `act-${i}`,
            title: a.title,
            description: a.detail,
            type: "engagement" as const,
            timestamp: a.timestamp
              ? new Date(a.timestamp).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })
              : "Recently",
          }))
        );
      })
      .catch(() => {
        setStats(STAT_CONFIG.map((cfg) => ({ ...cfg, value: 0 })));
      });
  }, []);

  return (
    <div className="space-y-6">
      <section
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        aria-label="Key metrics"
      >
        {stats.map((stat) => (
          <StatCard key={stat.id} stat={stat} />
        ))}
      </section>

      <DashboardCharts
        riskDistribution={riskDistribution}
        violationsByRule={violationsByRule}
      />

      <RecentActivities items={activities} />
    </div>
  );
}
