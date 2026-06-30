import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { AuditModulesGrid } from "@/components/dashboard/AuditModulesGrid";

export const metadata: Metadata = {
  title: "AI Audit Modules | AIML Audit",
  description: "22 AI-powered audit modules for journal, revenue, procurement, and more.",
};

export default function AiModulesPage() {
  return (
    <DashboardShell
      title="AI Audit Modules"
      subtitle="22 intelligent audit modules — open any active module from the catalog"
    >
      <AuditModulesGrid />
    </DashboardShell>
  );
}
