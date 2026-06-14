import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { RulesList } from "@/components/dashboard/RulesList";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Audit Rules | AIML Audit",
  description: "Rules master configuration",
};

export default function RulesPage() {
  return (
    <DashboardShell
      title="Audit Rules"
      subtitle="Configure audit rules, risk scores, and detection settings"
    >
      <RulesList />
    </DashboardShell>
  );
}
