import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { OrganizationMembers } from "@/components/dashboard/OrganizationMembers";
import { OrganizationSettings } from "@/components/dashboard/OrganizationSettings";
import { SettingsProfile } from "@/components/dashboard/SettingsProfile";
import { SubscriptionSettings } from "@/components/dashboard/SubscriptionSettings";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings | AIML Audit",
  description: "Account settings",
};

export default function SettingsPage() {
  return (
    <DashboardShell title="Settings" subtitle="Account and portal preferences">
      <div className="space-y-8">
        <OrganizationSettings />
        <OrganizationMembers />
        <SubscriptionSettings />
        <SettingsProfile />
      </div>
    </DashboardShell>
  );
}
