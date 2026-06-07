import {
  createPlaceholderMetadata,
  DashboardPlaceholderPage,
} from "@/components/dashboard/DashboardPlaceholderPage";

export const metadata = createPlaceholderMetadata("Audit Engagements");

export default function EngagementsPage() {
  return (
    <DashboardPlaceholderPage
      title="Audit Engagements"
      subtitle="Track statutory, internal, and tax audit engagements"
    />
  );
}
