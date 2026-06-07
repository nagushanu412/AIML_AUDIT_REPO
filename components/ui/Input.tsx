"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, label, error, hint, id, required, ...props },
  ref
) {
  const inputId = id ?? props.name;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-slate-700"
      >
        {label}
        {required && (
          <span className="ml-0.5 text-red-500" aria-hidden="true">
            *
          </span>
        )}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={
          error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
        }
        required={required}
        className={cn(
          "block w-full rounded-lg border bg-white/80 px-3.5 py-2.5 text-sm text-slate-900",
          "placeholder:text-slate-400 transition-colors duration-200",
          "focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500",
          error
            ? "border-red-400 focus:ring-red-500/30 focus:border-red-500"
            : "border-slate-200 hover:border-slate-300",
          className
        )}
        {...props}
      />
      {hint && !error && (
        <p id={`${inputId}-hint`} className="text-xs text-slate-500">
          {hint}
        </p>
      )}
      {error && (
        <p
          id={`${inputId}-error`}
          role="alert"
          className="text-xs font-medium text-red-600 animate-fade-in"
        >
          {error}
        </p>
      )}
    </div>
  );
});
