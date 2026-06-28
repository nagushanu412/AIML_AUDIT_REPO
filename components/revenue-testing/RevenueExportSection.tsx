"use client";

import { useState } from "react";
import { FileDown, FileSpreadsheet, FileText } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { generateReport } from "@/lib/api";

interface RevenueExportSectionProps {
  projectId: string;
}

const REPORT_TYPES = {
  excel: "revenue_audit_excel",
  pdf: "revenue_audit_pdf",
  wp: "revenue_working_paper",
} as const;

export function RevenueExportSection({ projectId }: RevenueExportSectionProps) {
  const [exporting, setExporting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (type: keyof typeof REPORT_TYPES) => {
    setExporting(type);
    setMessage(null);
    setError(null);
    try {
      const report = await generateReport(projectId, REPORT_TYPES[type]);
      setMessage(`${report.file_name} generated. View on Reports page.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(null);
    }
  };

  return (
    <SectionCard title="Export Revenue Working Papers" description="Generate enterprise audit reports for the revenue workstream.">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Button type="button" variant="secondary" size="md" isLoading={exporting === "excel"} disabled={exporting !== null} onClick={() => handleExport("excel")}>
          <FileSpreadsheet className="h-4 w-4" /> Export Excel
        </Button>
        <Button type="button" variant="secondary" size="md" isLoading={exporting === "pdf"} disabled={exporting !== null} onClick={() => handleExport("pdf")}>
          <FileDown className="h-4 w-4" /> Export PDF
        </Button>
        <Button type="button" variant="primary" size="md" className="bg-indigo-600 hover:bg-indigo-500" isLoading={exporting === "wp"} disabled={exporting !== null} onClick={() => handleExport("wp")}>
          <FileText className="h-4 w-4" /> Working Paper
        </Button>
      </div>
      {message && <p className="mt-3 text-sm font-medium text-emerald-600">{message}</p>}
      {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
    </SectionCard>
  );
}
