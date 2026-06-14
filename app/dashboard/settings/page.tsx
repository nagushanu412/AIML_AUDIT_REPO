import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { SettingsProfile } from "@/components/dashboard/SettingsProfile";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings | AIML Audit",
  description: "Account settings",
};

export default function SettingsPage() {
  return (
    <DashboardShell title="Settings" subtitle="Account and portal preferences">
      <SettingsProfile />
    </DashboardShell>
  );
}
