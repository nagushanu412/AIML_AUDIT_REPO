import { CheckCircle2, XCircle } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import {
  MANDATORY_COLUMNS,
  OPTIONAL_COLUMNS,
} from "@/lib/journal-entry-testing/constants";
import type { ValidationSummary } from "@/lib/journal-entry-testing/types";
import {
  formatIndianAmount,
  formatRecordCount,
} from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface DataValidationPanelProps {
  validation: ValidationSummary | null;
  isEmpty?: boolean;
}

export function DataValidationPanel({
  validation,
  isEmpty = false,
}: DataValidationPanelProps) {
  if (isEmpty) {
    return (
      <SectionCard
        title="Data Validation"
        description="Upload a file to validate column mapping and record totals."
      >
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 py-10 text-center dark:border-slate-700 dark:bg-slate-800/30">
          <XCircle
            className="h-10 w-10 text-slate-300 dark:text-slate-600"
            aria-hidden="true"
          />
          <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-400">
            No file uploaded
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Validation runs automatically after a successful upload.
          </p>
        </div>
      </SectionCard>
    );
  }

  if (!validation) return null;

  return (
    <SectionCard
      title="Data Validation"
      description="Column mapping and debit/credit balance checks."
    >
      <div
        className={cn(
          "mb-5 flex items-center gap-3 rounded-lg border px-4 py-3",
          validation.mandatoryValid
            ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/40"
            : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/40"
        )}
      >
        {validation.mandatoryValid ? (
          <CheckCircle2
            className="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400"
            aria-hidden="true"
          />
        ) : (
          <XCircle
            className="h-5 w-5 shrink-0 text-red-600 dark:text-red-400"
            aria-hidden="true"
          />
        )}
        <p
          className={cn(
            "text-sm font-semibold",
            validation.mandatoryValid
              ? "text-emerald-800 dark:text-emerald-300"
              : "text-red-800 dark:text-red-300"
          )}
        >
          {validation.mandatoryValid
            ? "✓ Mandatory Columns Validated"
            : "Mandatory columns missing or invalid"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Mandatory Columns
          </p>
          <ul className="flex flex-wrap gap-2" role="list">
            {MANDATORY_COLUMNS.map((col) => (
              <li
                key={col}
                className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                {col}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Optional Columns
          </p>
          <ul className="flex flex-wrap gap-2" role="list">
            {OPTIONAL_COLUMNS.map((col) => (
              <li
                key={col}
                className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400"
              >
                {col}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-3 dark:border-slate-700">
        <Stat label="Total Records" value={formatRecordCount(validation.totalRecords)} />
        <Stat
          label="Total Debit Amount"
          value={`₹ ${formatIndianAmount(validation.totalDebit)}`}
        />
        <Stat
          label="Total Credit Amount"
          value={`₹ ${formatIndianAmount(validation.totalCredit)}`}
        />
      </div>
    </SectionCard>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800/50">
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 font-display text-lg font-bold text-slate-900 dark:text-white">
        {value}
      </p>
    </div>
  );
}
