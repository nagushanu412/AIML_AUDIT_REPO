"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  function Checkbox({ className, label, id, ...props }, ref) {
    const checkboxId = id ?? props.name;

    return (
      <label
        htmlFor={checkboxId}
        className={cn(
          "inline-flex cursor-pointer select-none items-center gap-2.5 text-sm text-slate-600",
          className
        )}
      >
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          className={cn(
            "h-4 w-4 rounded border-slate-300 text-brand-600",
            "focus:ring-2 focus:ring-brand-500/40 focus:ring-offset-0",
            "transition-colors cursor-pointer"
          )}
          {...props}
        />
        <span>{label}</span>
      </label>
    );
  }
);
