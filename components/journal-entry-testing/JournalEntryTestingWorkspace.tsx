"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AIAnalysisSection } from "@/components/journal-entry-testing/AIAnalysisSection";
import { AuditFindingsPanel } from "@/components/journal-entry-testing/AuditFindingsPanel";
import { ClientEngagementSection } from "@/components/journal-entry-testing/ClientEngagementSection";
import { ProjectSelectionSection } from "@/components/journal-entry-testing/ProjectSelectionSection";
import { ComingSoonFeatures } from "@/components/journal-entry-testing/ComingSoonFeatures";
import { DataValidationPanel } from "@/components/journal-entry-testing/DataValidationPanel";
import { ExportSection } from "@/components/journal-entry-testing/ExportSection";
import { FileUploadSection } from "@/components/journal-entry-testing/FileUploadSection";
import { FindingsTable } from "@/components/journal-entry-testing/FindingsTable";
import { ModulePageHeader } from "@/components/journal-entry-testing/ModulePageHeader";
import { ResultsSummaryCards } from "@/components/journal-entry-testing/ResultsSummaryCards";
import {
  fetchClients,
  fetchEngagements,
  fetchProjects,
  fetchFindings,
  fetchRiskScores,
  generateFindings,
  runRisk,
  runRules,
  uploadJournalFile,
} from "@/lib/api";
import type { ApiAuditFinding, ApiProject } from "@/lib/api/types";
import type {
  AnalysisStatus,
  AnalysisSummary,
  ClientOption,
  EngagementOption,
  JournalFinding,
  UploadedFileInfo,
  ValidationSummary,
} from "@/lib/journal-entry-testing/types";

function formatEngagementPeriod(start?: string | null, end?: string | null): string {
  if (!start && !end) return "—";
  const fmt = (d: string) =>
    new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  if (start && end) return `${fmt(start)} to ${fmt(end)}`;
  return start ? fmt(start) : end ? fmt(end) : "—";
}

export function JournalEntryTestingWorkspace() {
  const [clients, setClients] = useState<ClientOption[]>([]);
  const [engagements, setEngagements] = useState<EngagementOption[]>([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [selectedEngagementId, setSelectedEngagementId] = useState("");
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [projectId, setProjectId] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [uploadedFile, setUploadedFile] = useState<UploadedFileInfo | null>(null);
  const [validation, setValidation] = useState<ValidationSummary | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle");
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null);
  const [findings, setFindings] = useState<JournalFinding[]>([]);
  const [auditFindings, setAuditFindings] = useState<ApiAuditFinding[]>([]);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    fetchClients()
      .then((rows) => setClients(rows.map((c) => ({ id: c.id, name: c.name }))))
      .catch(() => setLoadError("Could not load clients. Sign in and ensure the API is running."));
  }, []);

  useEffect(() => {
    if (!selectedClientId) {
      setEngagements([]);
      return;
    }
    fetchEngagements(selectedClientId)
      .then((rows) =>
        setEngagements(
          rows.map((e) => ({
            id: e.id,
            clientId: e.client_id,
            label: `${e.financial_year} — ${e.audit_type}`,
            auditPeriod: formatEngagementPeriod(e.start_date, e.end_date),
            financialYear: e.financial_year,
          }))
        )
      )
      .catch(() => setLoadError("Could not load engagements."));
  }, [selectedClientId]);

  useEffect(() => {
    if (!selectedEngagementId) {
      setProjects([]);
      setProjectId("");
      return;
    }
    fetchProjects(selectedEngagementId)
      .then((rows) => {
        setProjects(rows);
        const journal = rows.find((p) => p.project_type === "journal_testing") ?? rows[0];
        setProjectId(journal?.id ?? "");
      })
      .catch(() => setLoadError("Could not load audit projects."));
  }, [selectedEngagementId]);

  const filteredEngagements = useMemo(
    () => engagements.filter((e) => e.clientId === selectedClientId),
    [engagements, selectedClientId]
  );

  const handleClientChange = useCallback((clientId: string) => {
    setSelectedClientId(clientId);
    setSelectedEngagementId("");
    setProjectId("");
    setProjects([]);
    setUploadedFile(null);
    setValidation(null);
    setAnalysisStatus("idle");
    setAnalysisSummary(null);
    setFindings([]);
    setAuditFindings([]);
    setAnalysisError(null);
  }, []);

  const handleFileChange = useCallback(
    async (file: UploadedFileInfo | null) => {
      setUploadedFile(file);
      setAnalysisStatus("idle");
      setAnalysisSummary(null);
      setFindings([]);
      setAuditFindings([]);
      setAnalysisError(null);

      if (!file?.rawFile || !projectId) {
        setValidation(null);
        return;
      }

      setUploading(true);
      try {
        const result = await uploadJournalFile(projectId, file.rawFile);
        setValidation({
          mandatoryValid: result.validation.is_valid && result.entries_imported > 0,
          totalRecords: result.entries_imported,
          totalDebit: result.validation.total_debit,
          totalCredit: result.validation.total_credit,
        });
        setUploadedFile({
          ...file,
          recordCount: result.entries_imported,
        });
      } catch (err) {
        setValidation(null);
        setAnalysisError(err instanceof Error ? err.message : "Upload failed.");
      } finally {
        setUploading(false);
      }
    },
    [projectId]
  );

  const canRunAnalysis = Boolean(
    selectedClientId &&
      selectedEngagementId &&
      projectId &&
      uploadedFile &&
      validation?.mandatoryValid &&
      !uploading
  );

  const handleRunAnalysis = async () => {
    if (!canRunAnalysis || !projectId) return;

    setAnalysisStatus("loading");
    setAnalysisError(null);

    try {
      await runRules(projectId);
      const riskResult = await runRisk(projectId);
      await generateFindings(projectId);
      const [scores, groupedFindings] = await Promise.all([
        fetchRiskScores(projectId),
        fetchFindings(projectId),
      ]);
      setAuditFindings(groupedFindings);

      setAnalysisSummary({
        totalEntries: riskResult.total_entries_scored,
        highRisk: riskResult.high_risk,
        mediumRisk: riskResult.medium_risk,
        lowRisk: riskResult.low_risk,
      });

      setFindings(
        scores
          .filter((s) => s.total_score > 0)
          .map((s) => ({
            id: s.id,
            date: s.posting_date ?? "",
            voucherNumber: s.journal_id ?? "",
            accountName: s.account_name ?? "",
            debitAmount: Number(s.amount ?? 0),
            creditAmount: 0,
            riskScore: s.total_score,
            riskLevel: s.risk_category as JournalFinding["riskLevel"],
            aiExplanation: Object.entries(s.rule_breakdown)
              .map(([code, score]) => `${code}: +${score}`)
              .join("; "),
          }))
      );

      setAnalysisStatus("complete");
    } catch (err) {
      setAnalysisStatus("error");
      setAnalysisError(err instanceof Error ? err.message : "Analysis failed.");
    }
  };

  const showResults = analysisStatus === "complete" && analysisSummary;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ModulePageHeader />

      {loadError && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {loadError}
        </p>
      )}

      <ClientEngagementSection
        clients={clients}
        engagements={filteredEngagements}
        selectedClientId={selectedClientId}
        selectedEngagementId={selectedEngagementId}
        onClientChange={handleClientChange}
        onEngagementChange={setSelectedEngagementId}
      />

      <ProjectSelectionSection
        projects={projects}
        selectedProjectId={projectId}
        onProjectChange={setProjectId}
        disabled={!selectedEngagementId}
      />

      <FileUploadSection
        file={uploadedFile}
        onFileChange={handleFileChange}
        disabled={!selectedEngagementId || !projectId || uploading}
      />

      <DataValidationPanel validation={validation} isEmpty={!uploadedFile} />

      <AIAnalysisSection
        status={analysisStatus}
        onRunAnalysis={handleRunAnalysis}
        canRun={canRunAnalysis}
        errorMessage={analysisError}
      />

      {showResults && (
        <>
          <ResultsSummaryCards summary={analysisSummary} />
          <AuditFindingsPanel findings={auditFindings} />
          <FindingsTable findings={findings} />
          {projectId && <ExportSection projectId={projectId} />}
        </>
      )}

      <ComingSoonFeatures />
    </div>
  );
}
