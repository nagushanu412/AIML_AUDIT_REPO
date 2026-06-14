import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ProjectTypeWorkspace } from "@/components/audit-workstreams/ProjectTypeWorkspace";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Revenue Testing | AIML Audit",
  description: "Revenue testing workstream — modules #13 and #20",
};

export default function RevenueTestingPage() {
  return (
    <DashboardShell
      title="Revenue Testing"
      subtitle="Engagement workstream — not part of Journal Entry Testing"
    >
      <ProjectTypeWorkspace workstream="revenue_testing" />
    </DashboardShell>
  );
}
