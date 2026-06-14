"use client";

import { AlertCircle, Bot, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { FUTURE_RISK_FACTORS } from "@/lib/journal-entry-testing/constants";
import type { AnalysisStatus } from "@/lib/journal-entry-testing/types";
import { cn } from "@/lib/utils/cn";

interface AIAnalysisSectionProps {
  status: AnalysisStatus;
  onRunAnalysis: () => void;
  canRun: boolean;
  errorMessage?: string | null;
}

export function AIAnalysisSection({
  status,
  onRunAnalysis,
  canRun,
  errorMessage,
}: AIAnalysisSectionProps) {
  const isLoading = status === "loading";

  return (
    <SectionCard
      title="AI Analysis"
      description="Run intelligent risk scoring across uploaded journal entries."
    >
      <div className="rounded-lg border border-brand-100 bg-gradient-to-br from-brand-50/80 to-white p-4 dark:border-brand-900/50 dark:from-brand-950/40 dark:to-slate-900">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              Rule Engine + Risk Scoring
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Runs 7 audit rules from rules_master, scores violations, and generates findings.
            </p>
          </div>
        </div>

        <ul className="mt-4 flex flex-wrap gap-2" role="list">
          {FUTURE_RISK_FACTORS.map((factor) => (
            <li
              key={factor}
              className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-600"
            >
              <Sparkles
                className="h-3 w-3 text-brand-500"
                aria-hidden="true"
              />
              {factor}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Button
          type="button"
          variant="primary"
          size="lg"
          isLoading={isLoading}
          disabled={!canRun || isLoading}
          onClick={onRunAnalysis}
        >
          {isLoading ? "Running AI Analysis…" : "Run AI Analysis"}
        </Button>
        {!canRun && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Select client, engagement, and upload a validated file to continue.
          </p>
        )}
      </div>

      {status === "complete" && (
        <p className="mt-3 text-sm font-medium text-emerald-600 dark:text-emerald-400">
          Analysis complete. Review findings below.
        </p>
      )}

      {(status === "error" || errorMessage) && (
        <div
          role="alert"
          className={cn(
            "mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700",
            "dark:border-red-900 dark:bg-red-950/50 dark:text-red-300"
          )}
        >
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {errorMessage ?? "Analysis failed. Please try again."}
        </div>
      )}
    </SectionCard>
  );
}
