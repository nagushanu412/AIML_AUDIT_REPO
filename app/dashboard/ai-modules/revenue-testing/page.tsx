import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { RevenueTestingWorkspace } from "@/components/revenue-testing/RevenueTestingWorkspace";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Revenue Testing | AIML Audit",
  description: "Enterprise revenue substantive testing — invoice checking, GST validation, customer balance review",
};

export default function RevenueTestingPage() {
  return (
    <DashboardShell
      title="Revenue Testing"
      subtitle="Enterprise workstream — sales register upload, AI analysis, and exception reporting"
    >
      <RevenueTestingWorkspace />
    </DashboardShell>
  );
}
