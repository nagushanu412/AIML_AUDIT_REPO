import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { AuditModulesGrid } from "@/components/dashboard/AuditModulesGrid";
import { EngagementWorkstreamsPanel } from "@/components/dashboard/EngagementWorkstreamsPanel";

export const metadata: Metadata = {
  title: "AI Audit Modules | AIML Audit",
  description: "AI-powered audit modules for journal testing, ledger scrutiny, and more.",
};

export default function AiModulesPage() {
  return (
    <DashboardShell
      title="AI Audit Modules"
      subtitle="Run intelligent audit procedures across engagements"
    >
      <EngagementWorkstreamsPanel />
      <AuditModulesGrid />
    </DashboardShell>
  );
}
