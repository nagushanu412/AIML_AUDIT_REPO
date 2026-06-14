import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ReportsList } from "@/components/dashboard/ReportsList";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reports | AIML Audit",
  description: "Audit reports and working papers",
};

export default function ReportsPage() {
  return (
    <DashboardShell
      title="Reports"
      subtitle="Audit reports, exception summaries, and analytics exports"
    >
      <ReportsList />
    </DashboardShell>
  );
}
