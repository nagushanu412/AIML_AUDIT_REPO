import { BrandingPanel } from "@/components/auth/BrandingPanel";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen">
      <BrandingPanel />

      <section
        className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-4 py-12 sm:px-8 lg:px-12"
        aria-label="Sign in"
      >
        {/* Subtle background for right panel */}
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

        <div className="relative z-10 w-full max-w-md">
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
