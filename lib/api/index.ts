import { apiFetch, apiUpload } from "./client";
import type {
  ApiAuditFinding,
  ApiClient,
  ApiDashboardSummary,
  ApiEngagement,
  ApiLoginResponse,
  ApiModuleCatalog,
  ApiEngagementModule,
  ApiMessageResponse,
  ApiInvitePreview,
  ApiAcceptInviteResponse,
  ApiOrganization,
  ApiOrganizationCreate,
  ApiOrganizationMember,
  ApiOrganizationUpdate,
  ApiMemberInvite,
  ApiMemberUpdate,
  ApiSubscriptionPlan,
  ApiSubscriptionSummary,
  ApiProject,
  ApiReport,
  ApiRiskScore,
  ApiProcurementRiskScore,
  ApiProcurementRunRiskResponse,
  ApiProcurementRunRulesResponse,
  ApiProcurementUploadResponse,
  ApiRevenueRiskScore,
  ApiRevenueRunRiskResponse,
  ApiRevenueRunRulesResponse,
  ApiRevenueUploadResponse,
  ApiRule,
  ApiRuleUpdate,
  ApiRunRiskResponse,
  ApiRunRulesResponse,
  ApiUploadResponse,
  ApiUserProfile,
} from "./types";

export * from "./client";
export * from "./config";
export * from "./types";

export function loginApi(email: string, password: string) {
  return apiFetch<ApiLoginResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password }),
  });
}

export function registerApi(data: {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
  phone?: string;
}) {
  return apiFetch<ApiLoginResponse>("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify(data),
  });
}

export function refreshTokenApi(refreshToken: string) {
  return apiFetch<ApiLoginResponse>("/auth/refresh", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function logoutApi(refreshToken: string) {
  return apiFetch<ApiMessageResponse>("/auth/logout", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function forgotPasswordApi(email: string) {
  return apiFetch<ApiMessageResponse>("/auth/forgot-password", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email }),
  });
}

export function previewInviteApi(token: string) {
  return apiFetch<ApiInvitePreview>(
    `/auth/invite/preview?token=${encodeURIComponent(token)}`,
    { auth: false }
  );
}

export function acceptInviteApi(data: { token: string; password?: string }) {
  return apiFetch<ApiAcceptInviteResponse>("/auth/invite/accept", {
    method: "POST",
    auth: false,
    body: JSON.stringify(data),
  });
}

export function fetchClients() {
  return apiFetch<ApiClient[]>("/clients");
}

export function fetchEngagements(clientId?: string) {
  const qs = clientId ? `?client_id=${clientId}` : "";
  return apiFetch<ApiEngagement[]>(`/engagements${qs}`);
}

export function fetchProjects(engagementId?: string) {
  const qs = engagementId ? `?engagement_id=${engagementId}` : "";
  return apiFetch<ApiProject[]>(`/projects${qs}`);
}

export function uploadJournalFile(projectId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiUpload<ApiUploadResponse>(`/upload?project_id=${projectId}`, form);
}

export function uploadRevenueFile(projectId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiUpload<ApiRevenueUploadResponse>(`/revenue/upload?project_id=${projectId}`, form);
}

export function runRevenueRules(projectId: string) {
  return apiFetch<ApiRevenueRunRulesResponse>(`/revenue/run-rules?project_id=${projectId}`, {
    method: "POST",
  });
}

export function runRevenueRisk(projectId: string) {
  return apiFetch<ApiRevenueRunRiskResponse>(`/revenue/run-risk?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchRevenueRiskScores(projectId: string) {
  return apiFetch<ApiRevenueRiskScore[]>(`/revenue/risk-scores?project_id=${projectId}`);
}

export function generateRevenueFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/revenue/generate-findings?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchRevenueFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/revenue/findings?project_id=${projectId}`);
}

export function uploadProcurementFile(projectId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiUpload<ApiProcurementUploadResponse>(`/procurement/upload?project_id=${projectId}`, form);
}

export function runProcurementRules(projectId: string) {
  return apiFetch<ApiProcurementRunRulesResponse>(`/procurement/run-rules?project_id=${projectId}`, {
    method: "POST",
  });
}

export function runProcurementRisk(projectId: string) {
  return apiFetch<ApiProcurementRunRiskResponse>(`/procurement/run-risk?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchProcurementRiskScores(projectId: string) {
  return apiFetch<ApiProcurementRiskScore[]>(`/procurement/risk-scores?project_id=${projectId}`);
}

export function generateProcurementFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/procurement/generate-findings?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchProcurementFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/procurement/findings?project_id=${projectId}`);
}

export function runRules(projectId: string) {
  return apiFetch<ApiRunRulesResponse>(`/run-rules?project_id=${projectId}`, {
    method: "POST",
  });
}

export function runRisk(projectId: string) {
  return apiFetch<ApiRunRiskResponse>(`/run-risk?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchRiskScores(projectId: string) {
  return apiFetch<ApiRiskScore[]>(`/risk-scores?project_id=${projectId}`);
}

export function generateFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/generate-findings?project_id=${projectId}`, {
    method: "POST",
  });
}

export function fetchFindings(projectId: string) {
  return apiFetch<ApiAuditFinding[]>(`/findings?project_id=${projectId}`);
}

export function fetchRules() {
  return apiFetch<ApiRule[]>("/rules");
}

export function updateRule(id: string, data: ApiRuleUpdate) {
  return apiFetch<ApiRule>(`/rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function fetchReports(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return apiFetch<ApiReport[]>(`/reports${qs}`);
}

export function generateReport(projectId: string, reportType: string) {
  return apiFetch<ApiReport>(
    `/reports/generate?project_id=${projectId}&report_type=${encodeURIComponent(reportType)}`,
    { method: "POST" }
  );
}

export function createClient(data: {
  name: string;
  industry?: string;
  contact_person?: string;
}) {
  return apiFetch<ApiClient>("/clients", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function createEngagement(data: {
  client_id: string;
  financial_year: string;
  financial_year_end: string;
  audit_type?: string;
  large_value_threshold?: number;
}) {
  return apiFetch<ApiEngagement>("/engagements", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function createProject(data: {
  engagement_id: string;
  name: string;
  project_type?: string;
}) {
  return apiFetch<ApiProject>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchDashboardSummary() {
  return apiFetch<ApiDashboardSummary>("/dashboard/summary");
}

export function fetchMe() {
  return apiFetch<ApiUserProfile>("/auth/me");
}

export function fetchMyOrganization() {
  return apiFetch<ApiOrganization>("/organizations/me");
}

export function createOrganization(data: ApiOrganizationCreate) {
  return apiFetch<ApiOrganization>("/organizations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateMyOrganization(data: ApiOrganizationUpdate) {
  return apiFetch<ApiOrganization>("/organizations/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function fetchOrganizationMembers() {
  return apiFetch<ApiOrganizationMember[]>("/organizations/me/members");
}

export function inviteOrganizationMember(data: ApiMemberInvite) {
  return apiFetch<ApiOrganizationMember>("/organizations/me/members/invite", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateOrganizationMember(memberId: string, data: ApiMemberUpdate) {
  return apiFetch<ApiOrganizationMember>(`/organizations/me/members/${memberId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function removeOrganizationMember(memberId: string) {
  return apiFetch<ApiOrganizationMember>(`/organizations/me/members/${memberId}`, {
    method: "DELETE",
  });
}

export function fetchSubscriptionPlans() {
  return apiFetch<ApiSubscriptionPlan[]>("/subscriptions/plans");
}

export function fetchMySubscription() {
  return apiFetch<ApiSubscriptionSummary>("/subscriptions/me");
}

export function changeSubscriptionPlan(planCode: string) {
  return apiFetch<ApiSubscriptionSummary>("/subscriptions/me", {
    method: "PATCH",
    body: JSON.stringify({ plan_code: planCode }),
  });
}

export function fetchModuleCatalog() {
  return apiFetch<ApiModuleCatalog[]>("/modules/catalog");
}

export function fetchEngagementModules(engagementId: string) {
  return apiFetch<ApiEngagementModule[]>(`/engagements/${engagementId}/modules`);
}

export function enableEngagementModule(engagementId: string, moduleCode: string) {
  return apiFetch<ApiEngagementModule>(
    `/engagements/${engagementId}/modules/${moduleCode}/enable`,
    { method: "POST" }
  );
}

export function disableEngagementModule(engagementId: string, moduleCode: string) {
  return apiFetch<ApiEngagementModule>(
    `/engagements/${engagementId}/modules/${moduleCode}/disable`,
    { method: "POST" }
  );
}

export function updateClient(
  id: string,
  data: Partial<{ name: string; industry: string; status: string }>
) {
  return apiFetch<ApiClient>(`/clients/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteClient(id: string) {
  return apiFetch<void>(`/clients/${id}`, { method: "DELETE" });
}

export function updateEngagement(
  id: string,
  data: Partial<{
    financial_year: string;
    status: string;
    audit_type: string;
    financial_year_end: string;
    large_value_threshold: number;
  }>
) {
  return apiFetch<ApiEngagement>(`/engagements/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteEngagement(id: string) {
  return apiFetch<void>(`/engagements/${id}`, { method: "DELETE" });
}

export function updateProject(
  id: string,
  data: Partial<{ name: string; status: string; project_type: string }>
) {
  return apiFetch<ApiProject>(`/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteProject(id: string) {
  return apiFetch<void>(`/projects/${id}`, { method: "DELETE" });
}

export async function downloadReportFile(reportId: string, fileName: string) {
  const { getAccessToken } = await import("@/lib/auth/session");
  const { API_BASE_URL } = await import("./config");
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error("Download failed");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}
