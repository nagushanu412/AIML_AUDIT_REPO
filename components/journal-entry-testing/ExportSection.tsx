"use client";

import { useState } from "react";
import { FileDown, FileSpreadsheet, FileText } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { generateReport } from "@/lib/api";

interface ExportSectionProps {
  projectId: string;
  disabled?: boolean;
}

const REPORT_TYPES = {
  excel: "journal_audit_excel",
  pdf: "journal_audit_pdf",
  wp: "working_paper",
} as const;

export function ExportSection({ projectId, disabled = false }: ExportSectionProps) {
  const [exporting, setExporting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (type: keyof typeof REPORT_TYPES) => {
    setExporting(type);
    setMessage(null);
    setError(null);

    try {
      const report = await generateReport(projectId, REPORT_TYPES[type]);
      setMessage(
        `${report.file_name} generated. View it on the Reports page.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(null);
    }
  };

  return (
    <SectionCard
      title="Export"
      description="Generate audit reports and working papers for the audit file."
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Button
          type="button"
          variant="secondary"
          size="md"
          disabled={disabled || exporting !== null}
          isLoading={exporting === "excel"}
          onClick={() => handleExport("excel")}
        >
          <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
          Export Excel Report
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="md"
          disabled={disabled || exporting !== null}
          isLoading={exporting === "pdf"}
          onClick={() => handleExport("pdf")}
        >
          <FileDown className="h-4 w-4" aria-hidden="true" />
          Export PDF Report
        </Button>
        <Button
          type="button"
          variant="primary"
          size="md"
          disabled={disabled || exporting !== null}
          isLoading={exporting === "wp"}
          onClick={() => handleExport("wp")}
        >
          <FileText className="h-4 w-4" aria-hidden="true" />
          Generate Working Paper
        </Button>
      </div>

      {message && (
        <p className="mt-3 text-sm font-medium text-emerald-600 dark:text-emerald-400">
          {message}
        </p>
      )}
      {error && (
        <p className="mt-3 text-sm font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </SectionCard>
  );
}
