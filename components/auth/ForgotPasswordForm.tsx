"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft, Mail } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { forgotPassword } from "@/lib/auth/auth";
import { PRODUCT_NAME } from "@/lib/auth/constants";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      setMessage(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white/70 p-8 shadow-glass-lg backdrop-blur-xl ring-1 ring-slate-900/5">
      <header className="mb-6">
        <h1 className="font-display text-2xl font-bold text-slate-900">
          Forgot password
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter your work email and we&apos;ll send reset instructions when email delivery is configured.
        </p>
      </header>

      {message && (
        <p className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </p>
      )}
      {error && (
        <div className="mb-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Work email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@firm.com"
          required
        />
        <Button type="submit" variant="primary" size="lg" className="w-full" isLoading={loading}>
          <Mail className="h-4 w-4" />
          Send reset link
        </Button>
      </form>

      <Link
        href="/"
        className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {PRODUCT_NAME} sign in
      </Link>
    </div>
  );
}
