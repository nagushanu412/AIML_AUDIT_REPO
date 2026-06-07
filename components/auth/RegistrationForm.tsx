"use client";

import { FormEvent, useCallback, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  CreditCard,
  Lock,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { mockRegister } from "@/lib/auth/mockRegistration";
import {
  REGISTRATION_PRODUCT_NAME,
  TRIAL_BADGES,
} from "@/lib/auth/registrationConstants";
import type {
  RegistrationFormData,
  RegistrationValidationErrors,
} from "@/lib/auth/registrationTypes";
import {
  hasRegistrationErrors,
  validateRegistrationForm,
} from "@/lib/auth/validateRegistration";
import { cn } from "@/lib/utils/cn";

const INITIAL_FORM: RegistrationFormData = {
  companyName: "",
  adminFullName: "",
  businessEmail: "",
  mobileNumber: "",
  password: "",
  confirmPassword: "",
  agreeToTerms: false,
};

export function RegistrationForm() {
  const router = useRouter();
  const [form, setForm] = useState<RegistrationFormData>(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState<RegistrationValidationErrors>(
    {}
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const updateField = useCallback(
    <K extends keyof RegistrationFormData>(
      key: K,
      value: RegistrationFormData[K]
    ) => {
      setForm((prev) => ({ ...prev, [key]: value }));
      setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
    },
    []
  );

  const clearMessages = useCallback(() => {
    setFormError(null);
    setSuccessMessage(null);
  }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearMessages();

    const validation = validateRegistrationForm(form);
    if (hasRegistrationErrors(validation)) {
      setFieldErrors(validation);
      return;
    }

    setIsLoading(true);

    try {
      const result = await mockRegister(form);

      if (result.success) {
        const emailForLogin = form.businessEmail.trim();
        setSuccessMessage(
          `Welcome to ${REGISTRATION_PRODUCT_NAME}! Your 14-day free trial is ready. Redirecting to sign in…`
        );
        setForm(INITIAL_FORM);

        // Redirect to sign-in with a success banner and optional email prefill.
        // TODO: After Django integration, redirect after email verification and tenant provisioning.
        setTimeout(() => {
          const nextUrl = `/?registered=1&email=${encodeURIComponent(
            emailForLogin
          )}`;
          router.push(nextUrl);
        }, 900);
        return;
      }

      setFormError(result.error ?? "Registration failed. Please try again.");
    } catch {
      setFormError("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full max-w-lg flex-col animate-slide-up">
      {/* Mobile branding */}
      <div className="mb-6 flex items-center gap-3 lg:hidden">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 shadow-lg shadow-brand-600/30">
          <ShieldCheck className="h-5 w-5 text-white" strokeWidth={1.75} />
        </div>
        <div>
          <p className="font-display text-base font-bold text-slate-900">
            {REGISTRATION_PRODUCT_NAME}
          </p>
          <p className="text-xs text-slate-500">Company onboarding</p>
        </div>
      </div>

      {/* Trial highlights — mobile */}
      <div className="mb-6 flex flex-wrap gap-2 lg:hidden">
        {TRIAL_BADGES.slice(0, 2).map((badge) => (
          <span
            key={badge.id}
            className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-200/60"
          >
            {badge.id === "trial" ? (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <CreditCard className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {badge.label}
          </span>
        ))}
      </div>

      <div
        className={cn(
          "rounded-2xl border border-white/60 bg-white/70 p-6 shadow-glass-lg backdrop-blur-xl sm:p-8",
          "ring-1 ring-slate-900/5"
        )}
      >
        <header className="mb-6 text-center sm:text-left">
          <div className="mb-3 hidden flex-wrap gap-2 lg:flex">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200/60">
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
              14-Day Free Trial
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200/60">
              <CreditCard className="h-3.5 w-3.5" aria-hidden="true" />
              No credit card required
            </span>
          </div>

          <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
            Create your company account
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Set up your firm on our secure, multi-tenant audit platform.
          </p>
        </header>

        {(formError || successMessage) && (
          <div
            role="alert"
            className={cn(
              "mb-6 flex gap-3 rounded-lg border px-4 py-3 text-sm animate-fade-in",
              successMessage
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-800"
            )}
          >
            {successMessage ? (
              <CheckCircle2
                className="mt-0.5 h-4 w-4 shrink-0"
                aria-hidden="true"
              />
            ) : (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            )}
            <p>{successMessage ?? formError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Input
            id="companyName"
            name="companyName"
            label="Company Name"
            placeholder="Acme Audit Partners LLP"
            autoComplete="organization"
            required
            value={form.companyName}
            onChange={(e) => updateField("companyName", e.target.value)}
            error={fieldErrors.companyName}
            disabled={isLoading}
          />

          <Input
            id="adminFullName"
            name="adminFullName"
            label="Admin Full Name"
            placeholder="Priya Sharma"
            autoComplete="name"
            required
            value={form.adminFullName}
            onChange={(e) => updateField("adminFullName", e.target.value)}
            error={fieldErrors.adminFullName}
            disabled={isLoading}
          />

          <Input
            id="businessEmail"
            name="businessEmail"
            type="email"
            label="Business Email"
            placeholder="admin@yourfirm.com"
            autoComplete="email"
            required
            value={form.businessEmail}
            onChange={(e) => updateField("businessEmail", e.target.value)}
            error={fieldErrors.businessEmail}
            disabled={isLoading}
          />

          <Input
            id="mobileNumber"
            name="mobileNumber"
            type="tel"
            label="Mobile Number"
            placeholder="+91 98765 43210"
            autoComplete="tel"
            required
            value={form.mobileNumber}
            onChange={(e) => updateField("mobileNumber", e.target.value)}
            error={fieldErrors.mobileNumber}
            disabled={isLoading}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <PasswordInput
              id="password"
              name="password"
              label="Password"
              placeholder="Minimum 8 characters"
              autoComplete="new-password"
              required
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              error={fieldErrors.password}
              disabled={isLoading}
            />

            <PasswordInput
              id="confirmPassword"
              name="confirmPassword"
              label="Confirm Password"
              placeholder="Re-enter password"
              autoComplete="new-password"
              required
              value={form.confirmPassword}
              onChange={(e) => updateField("confirmPassword", e.target.value)}
              error={fieldErrors.confirmPassword}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-1.5 pt-1">
            <label
              htmlFor="agreeToTerms"
              className="inline-flex cursor-pointer select-none items-start gap-2.5 text-sm text-slate-600"
            >
              <input
                type="checkbox"
                id="agreeToTerms"
                name="agreeToTerms"
                checked={form.agreeToTerms}
                onChange={(e) => updateField("agreeToTerms", e.target.checked)}
                disabled={isLoading}
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600",
                  "focus:ring-2 focus:ring-brand-500/40 focus:ring-offset-0",
                  "transition-colors cursor-pointer",
                  fieldErrors.agreeToTerms && "border-red-400"
                )}
              />
              <span>
                I agree to the{" "}
                <Link
                  href="/terms"
                  className="font-medium text-brand-600 hover:text-brand-500 focus-visible:outline-none focus-visible:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  Terms
                </Link>{" "}
                and{" "}
                <Link
                  href="/privacy"
                  className="font-medium text-brand-600 hover:text-brand-500 focus-visible:outline-none focus-visible:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  Privacy Policy
                </Link>
              </span>
            </label>
            {fieldErrors.agreeToTerms && (
              <p
                id="agreeToTerms-error"
                role="alert"
                className="text-xs font-medium text-red-600 animate-fade-in"
              >
                {fieldErrors.agreeToTerms}
              </p>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={isLoading}
            disabled={isLoading}
            className="mt-2"
          >
            {isLoading ? "Creating account…" : "Create Free Trial Account"}
          </Button>
        </form>

        <div className="mt-5 flex items-center justify-center gap-4 border-t border-slate-100 pt-5 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
            Secure &amp; encrypted
          </span>
          <span className="hidden h-3 w-px bg-slate-200 sm:block" aria-hidden="true" />
          <span className="hidden sm:inline">Multi-company SaaS platform</span>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link
            href="/"
            className="font-semibold text-brand-600 hover:text-brand-500 focus-visible:outline-none focus-visible:underline"
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
