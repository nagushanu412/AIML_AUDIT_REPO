import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { JournalEntryTestingWorkspace } from "@/components/journal-entry-testing/JournalEntryTestingWorkspace";
import { MODULE_TITLE } from "@/lib/journal-entry-testing/constants";

export const metadata: Metadata = {
  title: `${MODULE_TITLE} | AIML Audit`,
  description:
    "AI-powered journal entry analysis for high-risk transactions and audit exceptions.",
};

export default function JournalEntryTestingPage() {
  return (
    <DashboardShell title={MODULE_TITLE} subtitle="Journal Entry Testing Workspace">
      <JournalEntryTestingWorkspace />
    </DashboardShell>
  );
}
