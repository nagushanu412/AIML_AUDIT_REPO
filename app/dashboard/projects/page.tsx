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
      subtitle="Audit projects mapped to the 22-module AI Audit catalog"
    >
      <ProjectsList />
    </DashboardShell>
  );
}
