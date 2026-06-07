import {
  createPlaceholderMetadata,
  DashboardPlaceholderPage,
} from "@/components/dashboard/DashboardPlaceholderPage";

export const metadata = createPlaceholderMetadata("Documents");

export default function DocumentsPage() {
  return (
    <DashboardPlaceholderPage
      title="Documents"
      subtitle="Working papers, schedules, and supporting documentation"
    />
  );
}
