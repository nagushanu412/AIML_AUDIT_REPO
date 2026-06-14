import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ProjectTypeWorkspace } from "@/components/audit-workstreams/ProjectTypeWorkspace";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Procurement Testing | AIML Audit",
  description: "Procurement testing workstream — modules #5, #6, and #7",
};

export default function ProcurementTestingPage() {
  return (
    <DashboardShell
      title="Procurement Testing"
      subtitle="Engagement workstream — not part of Journal Entry Testing"
    >
      <ProjectTypeWorkspace workstream="procurement_testing" />
    </DashboardShell>
  );
}
