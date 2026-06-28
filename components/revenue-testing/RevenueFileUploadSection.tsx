"use client";

import { useCallback, useRef, useState } from "react";
import { AlertCircle, FileSpreadsheet, RefreshCw, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { ACCEPTED_FILE_TYPES, MANDATORY_COLUMNS } from "@/lib/revenue-testing/constants";
import type { UploadedFileInfo } from "@/lib/revenue-testing/types";
import { formatFileSize, formatRecordCount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface RevenueFileUploadSectionProps {
  file: UploadedFileInfo | null;
  onFileChange: (file: UploadedFileInfo | null) => void;
  disabled?: boolean;
}

export function RevenueFileUploadSection({
  file,
  onFileChange,
  disabled = false,
}: RevenueFileUploadSectionProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(
    (raw: File) => {
      setError(null);
      if (!raw.name.toLowerCase().endsWith(".xlsx")) {
        setError("Only .xlsx sales register files are supported.");
        return;
      }
      onFileChange({
        name: raw.name,
        sizeBytes: raw.size,
        recordCount: 0,
        uploadedAt: new Date(),
        rawFile: raw,
      });
    },
    [onFileChange]
  );

  return (
    <SectionCard
      title="Sales Register Upload"
      description="Upload revenue / sales invoice register (.xlsx) for enterprise substantive testing."
      className="border-indigo-100/80 dark:border-indigo-900/30"
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_FILE_TYPES.join(",")}
        className="sr-only"
        onChange={(e) => {
          const selected = e.target.files?.[0];
          if (selected) processFile(selected);
          e.target.value = "";
        }}
        disabled={disabled}
      />

      <p className="mb-3 text-xs text-slate-500">
        Required columns: {MANDATORY_COLUMNS.join(", ")}
      </p>

      {!file ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (!disabled && e.dataTransfer.files[0]) processFile(e.dataTransfer.files[0]);
          }}
          className={cn(
            "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
            dragOver
              ? "border-indigo-400 bg-indigo-50/50"
              : "border-slate-200 bg-slate-50/50 dark:border-slate-600 dark:bg-slate-800/30",
            disabled && "pointer-events-none opacity-60"
          )}
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
            <Upload className="h-7 w-7" strokeWidth={1.5} aria-hidden="true" />
          </div>
          <p className="mt-4 text-sm font-medium text-slate-900 dark:text-white">
            Drag and drop sales register (.xlsx)
          </p>
          <Button
            type="button"
            variant="primary"
            size="md"
            className="mt-5 bg-indigo-600 hover:bg-indigo-500"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Upload Sales Register
          </Button>
          <p className="mt-3 text-xs text-slate-500">
            Sample: database/sample_revenue_invoices.xlsx
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-indigo-100 bg-indigo-50/30 p-4 dark:border-indigo-900/50">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                <FileSpreadsheet className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p className="font-medium text-slate-900 dark:text-white">{file.name}</p>
                <p className="mt-0.5 text-sm text-slate-500">
                  {formatRecordCount(file.recordCount)} invoices · {formatFileSize(file.sizeBytes)}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" size="sm" disabled={disabled} onClick={() => inputRef.current?.click()}>
                <RefreshCw className="h-4 w-4" /> Replace
              </Button>
              <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => onFileChange(null)}>
                <Trash2 className="h-4 w-4" /> Remove
              </Button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div role="alert" className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
    </SectionCard>
  );
}
