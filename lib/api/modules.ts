import { apiFetch, apiUpload } from "./client";
import type {
  ApiAuditFinding,
  ApiGenericFindingsResponse,
  ApiGenericRunRiskResponse,
  ApiGenericRunRulesResponse,
  ApiGenericUploadResponse,
  ApiModuleWorkspaceConfig,
  ApiReport,
} from "./types";

export const MODULE_CODES = {
  journal: "JOURNAL_ENTRY_TESTING",
  revenue: "REVENUE_TESTING",
  procurement: "PROCUREMENT_TESTING",
} as const;

export type ModuleCode = (typeof MODULE_CODES)[keyof typeof MODULE_CODES];

export function fetchModuleWorkspaceConfig(moduleCode: ModuleCode) {
  return apiFetch<ApiModuleWorkspaceConfig>(
    `/modules/${encodeURIComponent(moduleCode)}/workspace-config`
  );
}

export function uploadModuleFile(moduleCode: ModuleCode, projectId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiUpload<ApiGenericUploadResponse>(
    `/modules/${encodeURIComponent(moduleCode)}/upload?project_id=${projectId}`,
    form
  );
}

export function runModuleRules(moduleCode: ModuleCode, projectId: string) {
  return apiFetch<ApiGenericRunRulesResponse>(
    `/modules/${encodeURIComponent(moduleCode)}/run-rules?project_id=${projectId}`,
    { method: "POST" }
  );
}

export function runModuleRisk(moduleCode: ModuleCode, projectId: string) {
  return apiFetch<ApiGenericRunRiskResponse>(
    `/modules/${encodeURIComponent(moduleCode)}/run-risk?project_id=${projectId}`,
    { method: "POST" }
  );
}

export function fetchModuleRiskScores(moduleCode: ModuleCode, projectId: string) {
  return apiFetch<Record<string, unknown>[]>(
    `/modules/${encodeURIComponent(moduleCode)}/risk-scores?project_id=${projectId}`
  );
}

export function generateModuleFindings(moduleCode: ModuleCode, projectId: string) {
  return apiFetch<ApiGenericFindingsResponse>(
    `/modules/${encodeURIComponent(moduleCode)}/generate-findings?project_id=${projectId}`,
    { method: "POST" }
  );
}

export function fetchModuleFindings(moduleCode: ModuleCode, projectId: string) {
  return apiFetch<ApiGenericFindingsResponse>(
    `/modules/${encodeURIComponent(moduleCode)}/findings?project_id=${projectId}`
  );
}

export function generateModuleReport(
  moduleCode: ModuleCode,
  projectId: string,
  reportType?: string
) {
  const qs = reportType ? `&report_type=${encodeURIComponent(reportType)}` : "";
  return apiFetch<{ module_code: string; report: ApiReport }>(
    `/modules/${encodeURIComponent(moduleCode)}/reports/generate?project_id=${projectId}${qs}`,
    { method: "POST" }
  );
}

/** Map generic findings response to legacy flat array used by existing UI. */
export function flattenFindings(response: ApiGenericFindingsResponse): ApiAuditFinding[] {
  return response.items;
}
