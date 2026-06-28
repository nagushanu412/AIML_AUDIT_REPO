"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AuditFindingsPanel } from "@/components/journal-entry-testing/AuditFindingsPanel";
import { ClientEngagementSection } from "@/components/journal-entry-testing/ClientEngagementSection";
import { EnterpriseCapabilitiesPanel } from "@/components/revenue-testing/EnterpriseCapabilitiesPanel";
import { RevenueAnalysisSection } from "@/components/revenue-testing/RevenueAnalysisSection";
import { RevenueExportSection } from "@/components/revenue-testing/RevenueExportSection";
import { RevenueFileUploadSection } from "@/components/revenue-testing/RevenueFileUploadSection";
import { RevenueFindingsTable } from "@/components/revenue-testing/RevenueFindingsTable";
import { RevenueModuleHeader } from "@/components/revenue-testing/RevenueModuleHeader";
import { RevenueProjectSelectionSection } from "@/components/revenue-testing/RevenueProjectSelectionSection";
import { RevenueResultsSummaryCards } from "@/components/revenue-testing/RevenueResultsSummaryCards";
import { RevenueValidationPanel } from "@/components/revenue-testing/RevenueValidationPanel";
import { WorkflowStepper } from "@/components/revenue-testing/WorkflowStepper";
import {
  fetchClients,
  fetchEngagements,
  fetchProjects,
  fetchRevenueFindings,
  fetchRevenueRiskScores,
  generateRevenueFindings,
  runRevenueRisk,
  runRevenueRules,
  uploadRevenueFile,
} from "@/lib/api";
import type { ApiAuditFinding, ApiProject } from "@/lib/api/types";
import type {
  AnalysisStatus,
  ClientOption,
  EngagementOption,
  RevenueAnalysisSummary,
  RevenueFinding,
  RevenueValidationSummary,
  UploadedFileInfo,
  WorkflowStepId,
} from "@/lib/revenue-testing/types";

function formatEngagementPeriod(start?: string | null, end?: string | null): string {
  if (!start && !end) return "—";
  const fmt = (d: string) =>
    new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  if (start && end) return `${fmt(start)} to ${fmt(end)}`;
  return start ? fmt(start) : end ? fmt(end) : "—";
}

export function RevenueTestingWorkspace() {
  const [clients, setClients] = useState<ClientOption[]>([]);
  const [engagements, setEngagements] = useState<EngagementOption[]>([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [selectedEngagementId, setSelectedEngagementId] = useState("");
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [projectId, setProjectId] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [uploadedFile, setUploadedFile] = useState<UploadedFileInfo | null>(null);
  const [validation, setValidation] = useState<RevenueValidationSummary | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle");
  const [analysisSummary, setAnalysisSummary] = useState<RevenueAnalysisSummary | null>(null);
  const [findings, setFindings] = useState<RevenueFinding[]>([]);
  const [auditFindings, setAuditFindings] = useState<ApiAuditFinding[]>([]);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    fetchClients()
      .then((rows) => setClients(rows.map((c) => ({ id: c.id, name: c.name }))))
      .catch(() => setLoadError("Could not load clients."));
  }, []);

  useEffect(() => {
    if (!selectedClientId) { setEngagements([]); return; }
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
    if (!selectedEngagementId) { setProjects([]); setProjectId(""); return; }
    fetchProjects(selectedEngagementId)
      .then((rows) => {
        const revenueProjects = rows.filter((p) => p.project_type === "revenue_testing");
        setProjects(revenueProjects);
        setProjectId(revenueProjects[0]?.id ?? "");
      })
      .catch(() => setLoadError("Could not load projects."));
  }, [selectedEngagementId]);

  const filteredEngagements = useMemo(
    () => engagements.filter((e) => e.clientId === selectedClientId),
    [engagements, selectedClientId]
  );

  const resetAnalysis = useCallback(() => {
    setUploadedFile(null);
    setValidation(null);
    setAnalysisStatus("idle");
    setAnalysisSummary(null);
    setFindings([]);
    setAuditFindings([]);
    setAnalysisError(null);
  }, []);

  const handleClientChange = useCallback((clientId: string) => {
    setSelectedClientId(clientId);
    setSelectedEngagementId("");
    setProjectId("");
    setProjects([]);
    resetAnalysis();
  }, [resetAnalysis]);

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
        const result = await uploadRevenueFile(projectId, file.rawFile);
        setValidation({
          mandatoryValid: result.validation.is_valid && result.invoices_imported > 0,
          totalInvoices: result.invoices_imported,
          totalTaxable: result.total_taxable,
          totalGst: result.total_gst,
          totalRevenue: result.total_revenue,
        });
        setUploadedFile({ ...file, recordCount: result.invoices_imported });
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
    selectedClientId && selectedEngagementId && projectId && uploadedFile && validation?.mandatoryValid && !uploading
  );

  const handleRunAnalysis = async () => {
    if (!canRunAnalysis || !projectId) return;
    setAnalysisStatus("loading");
    setAnalysisError(null);
    try {
      await runRevenueRules(projectId);
      const riskResult = await runRevenueRisk(projectId);
      await generateRevenueFindings(projectId);
      const [scores, groupedFindings] = await Promise.all([
        fetchRevenueRiskScores(projectId),
        fetchRevenueFindings(projectId),
      ]);
      setAuditFindings(groupedFindings);
      setAnalysisSummary({
        totalInvoices: riskResult.total_invoices_scored,
        highRisk: riskResult.high_risk,
        mediumRisk: riskResult.medium_risk,
        lowRisk: riskResult.low_risk,
      });
      setFindings(
        scores
          .filter((s) => s.total_score > 0)
          .map((s) => ({
            id: s.id,
            invoiceDate: s.invoice_date ?? "",
            invoiceNo: s.invoice_no,
            customerName: s.customer_name,
            totalAmount: s.total_amount,
            gstAmount: s.gst_amount,
            paymentStatus: s.payment_status ?? "",
            riskScore: s.total_score,
            riskLevel: s.risk_category as RevenueFinding["riskLevel"],
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

  const completedSteps = useMemo(() => {
    const done = new Set<WorkflowStepId>();
    if (selectedClientId && selectedEngagementId && projectId) done.add("select");
    if (uploadedFile) done.add("upload");
    if (validation?.mandatoryValid) done.add("validate");
    if (analysisStatus === "complete") {
      done.add("analyze");
      done.add("review");
    }
    return done;
  }, [selectedClientId, selectedEngagementId, projectId, uploadedFile, validation, analysisStatus]);

  const activeStep: WorkflowStepId = useMemo(() => {
    if (analysisStatus === "complete") return "export";
    if (validation?.mandatoryValid) return "analyze";
    if (uploadedFile) return "validate";
    if (projectId) return "upload";
    return "select";
  }, [analysisStatus, validation, uploadedFile, projectId]);

  const showResults = analysisStatus === "complete" && analysisSummary;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <RevenueModuleHeader />
      <EnterpriseCapabilitiesPanel />
      <WorkflowStepper activeStep={activeStep} completedSteps={completedSteps} />

      {loadError && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{loadError}</p>
      )}

      <ClientEngagementSection
        clients={clients}
        engagements={filteredEngagements}
        selectedClientId={selectedClientId}
        selectedEngagementId={selectedEngagementId}
        onClientChange={handleClientChange}
        onEngagementChange={setSelectedEngagementId}
      />

      <RevenueProjectSelectionSection
        projects={projects}
        selectedProjectId={projectId}
        onProjectChange={setProjectId}
        disabled={!selectedEngagementId}
      />

      <RevenueFileUploadSection
        file={uploadedFile}
        onFileChange={handleFileChange}
        disabled={!selectedEngagementId || !projectId || uploading}
      />

      <RevenueValidationPanel validation={validation} isEmpty={!uploadedFile} />

      <RevenueAnalysisSection
        status={analysisStatus}
        onRunAnalysis={handleRunAnalysis}
        canRun={canRunAnalysis}
        errorMessage={analysisError}
      />

      {showResults && (
        <>
          <RevenueResultsSummaryCards summary={analysisSummary} />
          <AuditFindingsPanel findings={auditFindings} />
          <RevenueFindingsTable findings={findings} />
          {projectId && <RevenueExportSection projectId={projectId} />}
        </>
      )}
    </div>
  );
}
