import { AuthProvider } from "@/lib/auth/AuthProvider";
import { DashboardAuthGate } from "@/components/auth/DashboardAuthGate";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <DashboardAuthGate>{children}</DashboardAuthGate>
    </AuthProvider>
  );
}
