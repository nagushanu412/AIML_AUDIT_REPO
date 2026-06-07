import {
  createPlaceholderMetadata,
  DashboardPlaceholderPage,
} from "@/components/dashboard/DashboardPlaceholderPage";

export const metadata = createPlaceholderMetadata("Clients");

export default function ClientsPage() {
  return (
    <DashboardPlaceholderPage
      title="Clients"
      subtitle="Manage client firms and engagement relationships"
    />
  );
}
