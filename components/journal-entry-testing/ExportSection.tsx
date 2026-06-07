"use client";

import { useState } from "react";
import { FileDown, FileSpreadsheet, FileText } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";

interface ExportSectionProps {
  disabled?: boolean;
}

export function ExportSection({ disabled = false }: ExportSectionProps) {
  const [exporting, setExporting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleExport = async (type: "excel" | "pdf" | "wp") => {
    setExporting(type);
    setMessage(null);

    // TODO: GET /api/journal-entries/export/?format=excel|pdf|working-paper
    await new Promise((r) => setTimeout(r, 800));

    const labels = {
      excel: "Excel report",
      pdf: "PDF report",
      wp: "Working paper",
    };
    setMessage(`${labels[type]} generated (mock). Download will connect to Django API.`);
    setExporting(null);
  };

  return (
    <SectionCard
      title="Export"
      description="Download analysis results and working papers for the audit file."
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

      {disabled && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          Run AI analysis to enable exports.
        </p>
      )}

      {message && (
        <p className="mt-3 text-sm font-medium text-emerald-600 dark:text-emerald-400">
          {message}
        </p>
      )}
    </SectionCard>
  );
}
