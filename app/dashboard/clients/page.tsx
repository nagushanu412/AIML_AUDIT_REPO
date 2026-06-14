import { ClientsList } from "@/components/dashboard/ClientsList";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Clients | AIML Audit",
  description: "Manage audit clients",
};

export default function ClientsPage() {
  return (
    <DashboardShell
      title="Clients"
      subtitle="Manage client firms and engagement relationships"
    >
      <ClientsList />
    </DashboardShell>
  );
}
