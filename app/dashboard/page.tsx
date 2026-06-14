import type { Metadata } from "next";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { DashboardShell } from "@/components/dashboard/DashboardShell";

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
      <DashboardOverview />
    </DashboardShell>
  );
}
