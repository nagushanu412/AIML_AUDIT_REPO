import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ProcurementTestingWorkspace } from "@/components/procurement-testing/ProcurementTestingWorkspace";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Procurement Testing | AIML Audit",
  description: "Enterprise procurement substantive testing — vendor invoice upload, PO matching, duplicate payment detection",
};

export default function ProcurementTestingPage() {
  return (
    <DashboardShell
      title="Procurement Testing"
      subtitle="Enterprise workstream — vendor invoice register upload, AI analysis, and exception reporting"
    >
      <ProcurementTestingWorkspace />
    </DashboardShell>
  );
}
