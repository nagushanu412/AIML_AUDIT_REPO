import {
  createPlaceholderMetadata,
  DashboardPlaceholderPage,
} from "@/components/dashboard/DashboardPlaceholderPage";

export const metadata = createPlaceholderMetadata("Settings");

export default function SettingsPage() {
  return (
    <DashboardPlaceholderPage
      title="Settings"
      subtitle="Firm profile, users, roles, and platform configuration"
    />
  );
}
