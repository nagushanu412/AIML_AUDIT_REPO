"use client";

import { useCallback, useMemo, useState } from "react";
import { AIAnalysisSection } from "@/components/journal-entry-testing/AIAnalysisSection";
import { ClientEngagementSection } from "@/components/journal-entry-testing/ClientEngagementSection";
import { ComingSoonFeatures } from "@/components/journal-entry-testing/ComingSoonFeatures";
import { DataValidationPanel } from "@/components/journal-entry-testing/DataValidationPanel";
import { ExportSection } from "@/components/journal-entry-testing/ExportSection";
import { FileUploadSection } from "@/components/journal-entry-testing/FileUploadSection";
import { FindingsTable } from "@/components/journal-entry-testing/FindingsTable";
import { ModulePageHeader } from "@/components/journal-entry-testing/ModulePageHeader";
import { ResultsSummaryCards } from "@/components/journal-entry-testing/ResultsSummaryCards";
import {
  MOCK_ANALYSIS_SUMMARY,
  MOCK_CLIENTS,
  MOCK_ENGAGEMENTS,
  MOCK_FINDINGS,
  MOCK_VALIDATION,
} from "@/lib/journal-entry-testing/mockData";
import type {
  AnalysisStatus,
  AnalysisSummary,
  UploadedFileInfo,
  ValidationSummary,
} from "@/lib/journal-entry-testing/types";
import { delay } from "@/lib/journal-entry-testing/utils";

export function JournalEntryTestingWorkspace() {
  const [selectedClientId, setSelectedClientId] = useState("");
  const [selectedEngagementId, setSelectedEngagementId] = useState("");
  const [uploadedFile, setUploadedFile] = useState<UploadedFileInfo | null>(null);
  const [validation, setValidation] = useState<ValidationSummary | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle");
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(
    null
  );
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const filteredEngagements = useMemo(
    () => MOCK_ENGAGEMENTS.filter((e) => e.clientId === selectedClientId),
    [selectedClientId]
  );

  const handleClientChange = useCallback((clientId: string) => {
    setSelectedClientId(clientId);
    setSelectedEngagementId("");
    setAnalysisStatus("idle");
    setAnalysisSummary(null);
    setAnalysisError(null);
  }, []);

  const handleFileChange = useCallback((file: UploadedFileInfo | null) => {
    setUploadedFile(file);
    setAnalysisStatus("idle");
    setAnalysisSummary(null);
    setAnalysisError(null);

    if (file) {
      // TODO: POST file to Django — /api/journal-entries/validate/
      setValidation(MOCK_VALIDATION);
    } else {
      setValidation(null);
    }
  }, []);

  const canRunAnalysis = Boolean(
    selectedClientId &&
      selectedEngagementId &&
      uploadedFile &&
      validation?.mandatoryValid
  );

  const handleRunAnalysis = async () => {
    if (!canRunAnalysis) return;

    setAnalysisStatus("loading");
    setAnalysisError(null);

    try {
      // TODO: POST /api/journal-entries/analyze/ — Django + AIML risk engine
      await delay(2000);

      setAnalysisSummary(MOCK_ANALYSIS_SUMMARY);
      setAnalysisStatus("complete");
    } catch {
      setAnalysisStatus("error");
      setAnalysisError("AI analysis could not be completed. Please try again.");
    }
  };

  const showResults = analysisStatus === "complete" && analysisSummary;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ModulePageHeader />

      <ClientEngagementSection
        clients={MOCK_CLIENTS}
        engagements={filteredEngagements}
        selectedClientId={selectedClientId}
        selectedEngagementId={selectedEngagementId}
        onClientChange={handleClientChange}
        onEngagementChange={setSelectedEngagementId}
      />

      <FileUploadSection
        file={uploadedFile}
        onFileChange={handleFileChange}
        disabled={!selectedEngagementId}
      />

      <DataValidationPanel
        validation={validation}
        isEmpty={!uploadedFile}
      />

      <AIAnalysisSection
        status={analysisStatus}
        onRunAnalysis={handleRunAnalysis}
        canRun={canRunAnalysis}
        errorMessage={analysisError}
      />

      {showResults && (
        <>
          <ResultsSummaryCards summary={analysisSummary} />
          <FindingsTable findings={MOCK_FINDINGS} />
          <ExportSection />
        </>
      )}

      <ComingSoonFeatures />
    </div>
  );
}
