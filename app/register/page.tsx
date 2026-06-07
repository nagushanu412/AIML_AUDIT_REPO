import type { Metadata } from "next";
import { RegistrationBrandingPanel } from "@/components/auth/RegistrationBrandingPanel";
import { RegistrationForm } from "@/components/auth/RegistrationForm";
import { REGISTRATION_PRODUCT_NAME } from "@/lib/auth/registrationConstants";

export const metadata: Metadata = {
  title: `Register | ${REGISTRATION_PRODUCT_NAME}`,
  description:
    "Start your 14-day free trial. AI-powered audit automation for CA firms, auditors, and audit managers.",
  robots: { index: false, follow: false },
};

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen">
      <RegistrationBrandingPanel />

      <section
        className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-4 py-10 sm:px-8 lg:px-12"
        aria-label="Company registration"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-brand-50/40"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-brand-100/40 blur-3xl"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute -bottom-24 -left-24 h-80 w-80 rounded-full bg-slate-200/50 blur-3xl"
          aria-hidden="true"
        />

        <div className="relative z-10 w-full max-w-lg">
          <RegistrationForm />
        </div>
      </section>
    </main>
  );
}
