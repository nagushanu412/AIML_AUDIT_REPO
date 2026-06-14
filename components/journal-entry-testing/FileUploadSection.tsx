"use client";

import { useCallback, useRef, useState } from "react";
import {
  AlertCircle,
  FileSpreadsheet,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import { ACCEPTED_FILE_TYPES } from "@/lib/journal-entry-testing/constants";
import type { UploadedFileInfo } from "@/lib/journal-entry-testing/types";
import {
  formatFileSize,
  formatRecordCount,
} from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

interface FileUploadSectionProps {
  file: UploadedFileInfo | null;
  onFileChange: (file: UploadedFileInfo | null) => void;
  disabled?: boolean;
}

function isAcceptedFile(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPTED_FILE_TYPES.some((ext) => lower.endsWith(ext));
}

export function FileUploadSection({
  file,
  onFileChange,
  disabled = false,
}: FileUploadSectionProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(
    (raw: File) => {
      setError(null);

      if (!isAcceptedFile(raw.name)) {
        setError("Only .xlsx and .csv files are supported.");
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

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;

      const dropped = e.dataTransfer.files[0];
      if (dropped) processFile(dropped);
    },
    [disabled, processFile]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) processFile(selected);
    e.target.value = "";
  };

  const loadMockFile = () => {
    setError(null);
    setError("Use Upload File to select database/sample_journal_entries.xlsx from your machine.");
  };

  return (
    <SectionCard
      title="Excel Upload"
      description="Upload journal entry data in Excel or CSV format for AI analysis."
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.csv"
        className="sr-only"
        onChange={handleInputChange}
        disabled={disabled}
      />

      {!file ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={cn(
            "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
            dragOver
              ? "border-brand-400 bg-brand-50/50 dark:border-brand-500 dark:bg-brand-950/30"
              : "border-slate-200 bg-slate-50/50 dark:border-slate-600 dark:bg-slate-800/30",
            disabled && "pointer-events-none opacity-60"
          )}
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-brand-600 dark:bg-brand-900/50 dark:text-brand-400">
            <Upload className="h-7 w-7" strokeWidth={1.5} aria-hidden="true" />
          </div>
          <p className="mt-4 text-sm font-medium text-slate-900 dark:text-white">
            Drag and drop your file here
          </p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Supported: .xlsx, .csv
          </p>
          <Button
            type="button"
            variant="primary"
            size="md"
            className="mt-5"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Upload File
          </Button>
          <button
            type="button"
            onClick={loadMockFile}
            disabled={disabled}
            className="mt-3 text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
          >
            Or load sample Journal_Entries.xlsx
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-600 dark:bg-slate-800/50">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-900">
                <FileSpreadsheet className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p className="font-medium text-slate-900 dark:text-white">
                  {file.name}
                </p>
                <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  {formatRecordCount(file.recordCount)} Records ·{" "}
                  {formatFileSize(file.sizeBytes)}
                </p>
                <p className="mt-0.5 text-xs text-slate-400">
                  Uploaded{" "}
                  {file.uploadedAt.toLocaleString("en-IN", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={disabled}
                onClick={() => inputRef.current?.click()}
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Replace File
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={disabled}
                onClick={() => onFileChange(null)}
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                Remove File
              </Button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300"
        >
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {error}
        </div>
      )}
    </SectionCard>
  );
}
