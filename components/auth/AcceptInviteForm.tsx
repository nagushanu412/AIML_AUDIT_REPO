"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { acceptInvite, previewInvite } from "@/lib/auth/auth";
import { PRODUCT_NAME } from "@/lib/auth/constants";
import type { ApiInvitePreview } from "@/lib/api/types";

export function AcceptInviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [preview, setPreview] = useState<ApiInvitePreview | null>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError("This invitation link is missing or invalid.");
      setLoading(false);
      return;
    }

    previewInvite(token)
      .then(setPreview)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not load invitation.");
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !preview) return;

    setError(null);
    setSuccess(null);

    if (preview.requires_password) {
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setSubmitting(true);
    try {
      const result = await acceptInvite(
        token,
        preview.requires_password ? password : undefined
      );

      if (!result.success) {
        setError(result.error ?? "Could not accept invitation.");
        return;
      }

      if (result.requiresLogin) {
        setSuccess("Invitation accepted. Redirecting to sign in…");
        setTimeout(() => {
          router.push(`/?email=${encodeURIComponent(preview.email)}`);
        }, 900);
        return;
      }

      setSuccess("Welcome to AuditAI Platform. Redirecting to dashboard…");
      setTimeout(() => {
        router.push("/dashboard");
      }, 900);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-slate-500">Loading invitation…</p>
    );
  }

  return (
    <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white/70 p-8 shadow-glass-lg backdrop-blur-xl ring-1 ring-slate-900/5">
      <header className="mb-6 flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 shadow-lg shadow-brand-600/30">
          <ShieldCheck className="h-5 w-5 text-white" strokeWidth={1.75} />
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">
            Accept invitation
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Join your audit firm on {PRODUCT_NAME}.
          </p>
        </div>
      </header>

      {preview && (
        <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <p>
            <span className="font-medium text-slate-900">{preview.full_name}</span>{" "}
            ({preview.email})
          </p>
          <p className="mt-1">
            Organization: <span className="font-medium">{preview.organization_name}</span>
          </p>
          <p className="mt-1">
            Role: <span className="font-medium">{preview.role_label}</span>
          </p>
        </div>
      )}

      {success && (
        <p className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {success}
        </p>
      )}
      {error && (
        <div className="mb-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {preview && !success && (
        <form onSubmit={handleSubmit} className="space-y-4">
          {preview.requires_password ? (
            <>
              <PasswordInput
                label="Create password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
              <PasswordInput
                label="Confirm password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </>
          ) : (
            <p className="text-sm text-slate-600">
              You already have an account. Accept the invitation, then sign in with your
              existing password.
            </p>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={submitting}
          >
            {preview.requires_password ? "Set password and join" : "Accept invitation"}
          </Button>
        </form>
      )}

      <Link
        href="/"
        className="mt-6 inline-flex text-sm font-medium text-brand-600 hover:underline"
      >
        Back to sign in
      </Link>
    </div>
  );
}
