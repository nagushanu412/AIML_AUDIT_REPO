import { Suspense } from "react";
import { AcceptInviteForm } from "@/components/auth/AcceptInviteForm";

export default function AcceptInvitePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-brand-50/40 px-4 py-12">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading invitation…</p>}>
        <AcceptInviteForm />
      </Suspense>
    </main>
  );
}
