"use client";

import { AlertCircle, Bot, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { REVENUE_RULES } from "@/lib/revenue-testing/constants";
import type { AnalysisStatus } from "@/lib/revenue-testing/types";
import { cn } from "@/lib/utils/cn";

interface RevenueAnalysisSectionProps {
  status: AnalysisStatus;
  onRunAnalysis: () => void;
  canRun: boolean;
  errorMessage?: string | null;
}

export function RevenueAnalysisSection({
  status,
  onRunAnalysis,
  canRun,
  errorMessage,
}: RevenueAnalysisSectionProps) {
  const isLoading = status === "loading";

  return (
    <SectionCard
      title="Enterprise AI Analysis"
      description="Run 7 revenue-specific audit rules across invoice checking and customer balance modules."
      className="border-indigo-100/80 dark:border-indigo-900/30"
    >
      <div className="rounded-lg border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-violet-50/40 p-4 dark:from-indigo-950/40">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              Revenue Rule Engine + Risk Scoring
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Duplicate invoices, cut-off, GST mismatch, high-value, missing GSTIN, unpaid balances.
            </p>
          </div>
        </div>
        <ul className="mt-4 flex flex-wrap gap-2">
          {REVENUE_RULES.map((rule) => (
            <li
              key={rule.code}
              className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200"
            >
              <Sparkles className="h-3 w-3 text-indigo-500" aria-hidden="true" />
              {rule.name}
              <span className="text-[10px] text-indigo-500">{rule.module}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Button
          type="button"
          variant="primary"
          size="lg"
          className="bg-indigo-600 hover:bg-indigo-500"
          isLoading={isLoading}
          disabled={!canRun || isLoading}
          onClick={onRunAnalysis}
        >
          {isLoading ? "Running Revenue Analysis…" : "Run Revenue AI Analysis"}
        </Button>
        {!canRun && (
          <p className="text-sm text-slate-500">Complete engagement selection and upload a validated sales register.</p>
        )}
      </div>

      {status === "complete" && (
        <p className="mt-3 text-sm font-medium text-emerald-600">Analysis complete. Review revenue exceptions below.</p>
      )}

      {(status === "error" || errorMessage) && (
        <div role="alert" className={cn("mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700")}>
          <AlertCircle className="h-4 w-4 shrink-0" />
          {errorMessage ?? "Analysis failed."}
        </div>
      )}
    </SectionCard>
  );
}
