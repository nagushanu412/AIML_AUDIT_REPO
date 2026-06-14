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
      subtitle="Engagement workstreams mapped to AI Audit Modules from the 20-module catalog"
    >
      <ProjectsList />
    </DashboardShell>
  );
}
