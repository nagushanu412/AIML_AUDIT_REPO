import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ReportsList } from "@/components/dashboard/ReportsList";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Documents | AIML Audit",
  description: "Audit documents and generated reports",
};

export default function DocumentsPage() {
  return (
    <DashboardShell
      title="Documents"
      subtitle="Generated audit reports and working papers"
    >
      <ReportsList />
    </DashboardShell>
  );
}
