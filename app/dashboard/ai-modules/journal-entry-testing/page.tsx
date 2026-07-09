import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { AuditModuleWorkspace } from "@/components/modules/AuditModuleWorkspace";
import { JournalEntryTestingWorkspace } from "@/components/journal-entry-testing/JournalEntryTestingWorkspace";
import { MODULE_CODES } from "@/lib/api/modules";
import { MODULE_TITLE } from "@/lib/journal-entry-testing/constants";

export const metadata: Metadata = {
  title: `${MODULE_TITLE} | AIML Audit`,
  description:
    "AI-powered journal entry analysis for high-risk transactions and audit exceptions.",
};

export default function JournalEntryTestingPage() {
  return (
    <DashboardShell title={MODULE_TITLE} subtitle="Journal Entry Testing Workspace">
      <AuditModuleWorkspace moduleCode={MODULE_CODES.journal}>
        <JournalEntryTestingWorkspace />
      </AuditModuleWorkspace>
    </DashboardShell>
  );
}
