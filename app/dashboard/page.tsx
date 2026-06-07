import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { RecentActivities } from "@/components/dashboard/RecentActivities";
import { StatCard } from "@/components/dashboard/StatCard";
import { DASHBOARD_STATS } from "@/lib/dashboard/mockData";

export const metadata: Metadata = {
  title: "Dashboard | AIML Audit",
  description: "AIML Audit enterprise dashboard for auditors and CA firms.",
};

export default function DashboardPage() {
  return (
    <DashboardShell
      title="Dashboard"
      subtitle="Overview of clients, engagements, documents, and AI findings"
    >
      <div className="space-y-6">
        <section
          className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
          aria-label="Key metrics"
        >
          {DASHBOARD_STATS.map((stat) => (
            <StatCard key={stat.id} stat={stat} />
          ))}
        </section>

        <RecentActivities />
      </div>
    </DashboardShell>
  );
}
