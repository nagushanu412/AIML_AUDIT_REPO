import { EngagementsList } from "@/components/dashboard/EngagementsList";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Engagements | AIML Audit",
  description: "Track audit engagements",
};

export default function EngagementsPage() {
  return (
    <DashboardShell
      title="Audit Engagements"
      subtitle="Track statutory, internal, and tax audit engagements"
    >
      <EngagementsList />
    </DashboardShell>
  );
}
