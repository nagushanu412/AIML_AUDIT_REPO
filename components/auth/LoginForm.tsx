"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { SSOButton } from "@/components/auth/SSOButton";
import { DEMO_CREDENTIALS, PRODUCT_NAME } from "@/lib/auth/constants";
import {
  ensureValidSession,
  getRememberedEmail,
  login,
  validateLoginForm,
} from "@/lib/auth/auth";
import { mockGoogleSSO, mockMicrosoftSSO } from "@/lib/auth/mockAuth";
import type { AuthValidationErrors } from "@/lib/auth/types";
import { cn } from "@/lib/utils/cn";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState<"microsoft" | "google" | null>(
    null
  );
  const [fieldErrors, setFieldErrors] = useState<AuthValidationErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const remembered = getRememberedEmail();
    if (remembered) {
      setEmail(remembered);
      setRememberMe(true);
    }
    ensureValidSession().then((session) => {
      if (session) router.replace("/dashboard");
    });
  }, [router]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const registered = params.get("registered");
    const emailFromRegister = params.get("email");

    if (registered === "1") {
      setSuccessMessage(
        "Account created successfully. Please sign in to continue."
      );
      if (emailFromRegister) {
        setEmail((current) => current || emailFromRegister);
      }
    }
  }, []);

  const clearErrors = useCallback(() => {
    setFieldErrors({});
    setFormError(null);
  }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearErrors();
    setSuccessMessage(null);

    const validation = validateLoginForm(email, password);
    if (validation.email || validation.password) {
      setFieldErrors(validation);
      return;
    }

    setIsLoading(true);

    try {
      const result = await login({ email, password, rememberMe });

      if (result.success && result.session) {
        setSuccessMessage(
          `Welcome back, ${result.session.user.name}. Redirecting to dashboard…`
        );
        setTimeout(() => {
          router.push("/dashboard");
        }, 700);
        return;
      }

      if (result.requiresMfa) {
        setFormError("Two-factor authentication required. MFA flow not yet implemented.");
        return;
      }

      if (result.subscriptionValid === false) {
        setFormError("Your subscription is inactive. Please contact your administrator.");
        return;
      }

      setFormError(
        result.error ??
          "Sign in failed. Ensure the API is running at http://localhost:8000 and try again."
      );
    } catch {
      setFormError("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSSO = async (provider: "microsoft" | "google") => {
    clearErrors();
    setSuccessMessage(null);
    setSsoLoading(provider);

    try {
      const result =
        provider === "microsoft"
          ? await mockMicrosoftSSO()
          : await mockGoogleSSO();

      if (!result.success) {
        setFormError(result.error ?? "SSO sign-in failed.");
      }
    } finally {
      setSsoLoading(null);
    }
  };

  const isBusy = isLoading || ssoLoading !== null;

  return (
    <div className="flex w-full max-w-md flex-col animate-slide-up">
      {/* Mobile branding */}
      <div className="mb-8 flex items-center gap-3 lg:hidden">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 shadow-lg shadow-brand-600/30">
          <ShieldCheck className="h-5 w-5 text-white" strokeWidth={1.75} />
        </div>
        <div>
          <p className="font-display text-base font-bold text-slate-900">
            {PRODUCT_NAME}
          </p>
          <p className="text-xs text-slate-500">Secure firm portal</p>
        </div>
      </div>

      {/* Glass card */}
      <div
        className={cn(
          "rounded-2xl border border-white/60 bg-white/70 p-8 shadow-glass-lg backdrop-blur-xl",
          "ring-1 ring-slate-900/5"
        )}
      >
        <header className="mb-8 text-center sm:text-left">
          <h2 className="font-display text-2xl font-bold tracking-tight text-slate-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Access your audit engagements, AI modules, and workflow tools.
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
            {!successMessage && (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            )}
            <p>{successMessage ?? formError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <Input
            id="email"
            name="email"
            type="email"
            label="Work email"
            placeholder="you@auditfirm.com"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }));
            }}
            error={fieldErrors.email}
            disabled={isBusy}
          />

          <PasswordInput
            id="password"
            name="password"
            label="Password"
            placeholder="Enter your password"
            required
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password)
                setFieldErrors((p) => ({ ...p, password: undefined }));
            }}
            error={fieldErrors.password}
            disabled={isBusy}
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <Checkbox
              id="remember-me"
              name="rememberMe"
              label="Remember me"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={isBusy}
            />
            <Link
              href="/forgot-password"
              className="text-sm font-medium text-brand-600 hover:text-brand-500 focus-visible:outline-none focus-visible:underline"
            >
              Forgot password?
            </Link>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={isLoading}
            disabled={isBusy}
          >
            {isLoading ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase tracking-wider">
            <span className="bg-white/70 px-3 text-slate-400 backdrop-blur-sm">
              or continue with
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <SSOButton
            provider="microsoft"
            onClick={() => handleSSO("microsoft")}
            disabled={isBusy}
          />
          <SSOButton
            provider="google"
            onClick={() => handleSSO("google")}
            disabled={isBusy}
          />
        </div>

        <div className="mt-6 space-y-3">
          <Button
            type="button"
            variant="secondary"
            size="lg"
            fullWidth
            disabled={isBusy}
            onClick={() => {
              setFormError(null);
              setSuccessMessage(null);
              window.open("/signup", "_self");
            }}
          >
            Start Free Trial
          </Button>
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          Demo:{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600">
            {DEMO_CREDENTIALS.email}
          </code>{" "}
          /{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600">
            {DEMO_CREDENTIALS.password}
          </code>
        </p>
      </div>

      <p className="mt-6 text-center text-xs text-slate-400">
        By signing in you agree to our{" "}
        <Link href="/terms" className="underline hover:text-slate-600">
          Terms
        </Link>{" "}
        and{" "}
        <Link href="/privacy" className="underline hover:text-slate-600">
          Privacy Policy
        </Link>
        .
      </p>
    </div>
  );
}
