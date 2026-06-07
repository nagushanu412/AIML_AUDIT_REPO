import {
  createPlaceholderMetadata,
  DashboardPlaceholderPage,
} from "@/components/dashboard/DashboardPlaceholderPage";

export const metadata = createPlaceholderMetadata("Reports");

export default function ReportsPage() {
  return (
    <DashboardPlaceholderPage
      title="Reports"
      subtitle="Audit reports, exception summaries, and analytics"
    />
  );
}
