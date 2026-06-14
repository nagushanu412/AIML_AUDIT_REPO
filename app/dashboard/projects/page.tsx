import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ProjectsList } from "@/components/dashboard/ProjectsList";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Projects | AIML Audit",
  description: "Audit projects within engagements",
};

export default function ProjectsPage() {
  return (
    <DashboardShell
      title="Audit Projects"
      subtitle="Journal testing, revenue testing, and other audit workstreams"
    >
      <ProjectsList />
    </DashboardShell>
  );
}
