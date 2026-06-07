"use client";

import { forwardRef, useState, type InputHTMLAttributes } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export interface PasswordInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  error?: string;
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput(
    {
      className,
      label,
      error,
      id,
      required,
      autoComplete = "current-password",
      ...props
    },
    ref
  ) {
    const [visible, setVisible] = useState(false);
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
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            type={visible ? "text" : "password"}
            autoComplete={autoComplete}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={error ? `${inputId}-error` : undefined}
            required={required}
            className={cn(
              "block w-full rounded-lg border bg-white/80 py-2.5 pl-3.5 pr-11 text-sm text-slate-900",
              "placeholder:text-slate-400 transition-colors duration-200",
              "focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500",
              error
                ? "border-red-400 focus:ring-red-500/30 focus:border-red-500"
                : "border-slate-200 hover:border-slate-300",
              className
            )}
            {...props}
          />
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5",
              "text-slate-400 hover:text-slate-600 hover:bg-slate-100",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            )}
            aria-label={visible ? "Hide password" : "Show password"}
            tabIndex={-1}
          >
            {visible ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
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
  }
);
