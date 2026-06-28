import { CheckCircle2, XCircle } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { MANDATORY_COLUMNS, OPTIONAL_COLUMNS } from "@/lib/procurement-testing/constants";
import type { ProcurementValidationSummary } from "@/lib/procurement-testing/types";
import { formatIndianAmount, formatRecordCount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface ProcurementValidationPanelProps {
  validation: ProcurementValidationSummary | null;
  isEmpty?: boolean;
}

export function ProcurementValidationPanel({ validation, isEmpty = false }: ProcurementValidationPanelProps) {
  if (isEmpty) {
    return (
      <SectionCard title="Procurement Data Validation" description="Upload a vendor invoice register to validate schema and totals.">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 py-10 text-center">
          <XCircle className="h-10 w-10 text-slate-300" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-slate-600">No file uploaded</p>
        </div>
      </SectionCard>
    );
  }

  if (!validation) return null;

  return (
    <SectionCard title="Procurement Data Validation" description="Vendor invoice register schema, GST totals, and spend aggregation.">
      <div
        className={cn(
          "mb-5 flex items-center gap-3 rounded-lg border px-4 py-3",
          validation.mandatoryValid
            ? "border-emerald-200 bg-emerald-50"
            : "border-red-200 bg-red-50"
        )}
      >
        {validation.mandatoryValid ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-600" />
        )}
        <p className="text-sm font-semibold text-slate-800">
          {validation.mandatoryValid ? "Vendor invoice register validated — ready for AI analysis" : "Validation failed"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ColumnList title="Mandatory Columns" columns={MANDATORY_COLUMNS} filled />
        <ColumnList title="Optional Columns" columns={OPTIONAL_COLUMNS} />
      </div>

      <div className="mt-6 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-4">
        <Stat label="Total Invoices" value={formatRecordCount(validation.totalInvoices)} />
        <Stat label="Taxable Amount" value={`₹ ${formatIndianAmount(validation.totalTaxable)}`} />
        <Stat label="GST Amount" value={`₹ ${formatIndianAmount(validation.totalGst)}`} />
        <Stat label="Total Spend" value={`₹ ${formatIndianAmount(validation.totalSpend)}`} highlight />
      </div>
    </SectionCard>
  );
}

function ColumnList({ title, columns, filled }: { title: string; columns: readonly string[]; filled?: boolean }) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <ul className="flex flex-wrap gap-2">
        {columns.map((col) => (
          <li
            key={col}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium",
              filled
                ? "bg-teal-50 text-teal-800 ring-1 ring-teal-100"
                : "border border-slate-200 bg-white text-slate-600"
            )}
          >
            {col}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={cn("rounded-lg px-4 py-3", highlight ? "bg-teal-50 ring-1 ring-teal-100" : "bg-slate-50")}>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 font-display text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}
