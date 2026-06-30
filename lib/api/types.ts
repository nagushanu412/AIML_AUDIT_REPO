export interface ApiClient {
  id: string;
  name: string;
  industry?: string | null;
  status: string;
}

export interface ApiEngagement {
  id: string;
  client_id: string;
  financial_year: string;
  audit_type: string;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  financial_year_end: string;
  large_value_threshold: string;
}

export interface ApiProject {
  id: string;
  engagement_id: string;
  name: string;
  project_type: string;
  status: string;
  total_entries: number;
}

export interface ApiUploadResponse {
  project_id: string;
  validation: {
    is_valid: boolean;
    total_rows: number;
    total_debit: number;
    total_credit: number;
    errors: { message: string }[];
    warnings: { message: string }[];
  };
  entries_imported: number;
  message: string;
}

export interface ApiAuditFinding {
  id: string;
  rule_code: string;
  finding_title: string;
  observation: string;
  risk_level: string;
  impact: string;
  recommendation: string;
  affected_count: number;
  created_at: string;
}

export interface ApiReport {
  id: string;
  project_id: string;
  report_type: string;
  file_name: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ApiRule {
  id: string;
  rule_code: string;
  rule_name: string;
  description?: string | null;
  default_score: number;
  is_active: boolean;
  config_schema: Record<string, unknown>;
}

export interface ApiRuleUpdate {
  rule_name?: string;
  description?: string | null;
  default_score?: number;
  is_active?: boolean;
  config_schema?: Record<string, unknown>;
}

export interface ApiRunRulesResponse {
  project_id: string;
  total_entries_analyzed: number;
  total_violations_found: number;
  violations_by_rule: Record<string, number>;
  message: string;
}

export interface ApiRunRiskResponse {
  project_id: string;
  total_entries_scored: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  message: string;
}

export interface ApiRiskScore {
  id: string;
  journal_entry_id: string;
  total_score: number;
  risk_category: string;
  rule_breakdown: Record<string, number>;
  journal_id?: string;
  posting_date?: string;
  account_name?: string;
  amount?: string;
  user_id?: string;
}

export interface ApiDashboardSummary {
  total_clients: number;
  total_engagements: number;
  total_projects: number;
  total_journal_entries: number;
  total_violations: number;
  high_risk_entries: number;
  medium_risk_entries?: number;
  low_risk_entries?: number;
  risk_distribution?: Record<string, number>;
  violations_by_rule?: Record<string, number>;
  recent_activities: { type: string; title: string; detail: string; timestamp?: string }[];
}

export interface ApiUserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  company_name?: string | null;
  phone?: string | null;
  is_active: boolean;
}

export interface ApiOrganization {
  id: string;
  name: string;
  slug: string;
  status: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiOrganizationCreate {
  name: string;
  slug?: string;
  settings?: Record<string, unknown>;
}

export interface ApiOrganizationUpdate {
  name?: string;
  slug?: string;
  status?: string;
  settings?: Record<string, unknown>;
}

export interface ApiOrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  invited_at: string | null;
  joined_at: string;
  created_at: string;
  updated_at: string;
  invite_email_sent?: boolean;
  invite_link?: string | null;
}

export interface ApiMemberInvite {
  email: string;
  role?: string;
  full_name?: string;
}

export interface ApiMemberUpdate {
  role?: string;
  status?: string;
}

export interface ApiSubscriptionPlan {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  max_users: number;
  max_clients: number;
  max_engagements: number;
  max_storage_bytes: number;
  monthly_ai_credits: number;
  monthly_uploads: number;
  max_reports: number;
  enabled_module_codes: string[];
  api_rate_limit: number;
  support_level: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiUsageSnapshot {
  users: number;
  clients: number;
  engagements: number;
  reports: number;
  uploads: number;
  storage_bytes: number;
  ai_credits: number;
}

export interface ApiUsageLimits {
  max_users: number;
  max_clients: number;
  max_engagements: number;
  max_reports: number;
  monthly_uploads: number;
  max_storage_bytes: number;
  monthly_ai_credits: number;
  api_rate_limit: number;
}

export interface ApiSubscriptionSummary {
  subscription: {
    id: string;
    organization_id: string;
    status: string;
    started_at: string;
    ends_at?: string | null;
  };
  plan: ApiSubscriptionPlan;
  usage: ApiUsageSnapshot;
  limits: ApiUsageLimits;
}

export interface ApiLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id?: string | null;
  member_role?: string | null;
}

export interface ApiModuleCatalog {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  category: string;
  slug: string;
  icon: string;
  implementation_status: string;
  display_order: number;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiEngagementModule {
  id: string;
  engagement_id: string;
  module_code: string;
  module_name: string;
  module_slug: string;
  category: string;
  implementation_status: string;
  is_enabled: boolean;
  enabled_at: string;
}

export interface ApiEngagementTeamMember {
  id: string;
  engagement_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  is_primary: boolean;
  notes: string | null;
  assigned_by: string | null;
  assigned_by_name: string | null;
  assigned_at: string;
  removed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiEngagementTeamList {
  items: ApiEngagementTeamMember[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiEngagementTeamHistory {
  id: string;
  engagement_id: string;
  team_member_id: string | null;
  user_id: string;
  user_email: string;
  user_full_name: string;
  role: string;
  action: string;
  previous_role: string | null;
  changed_by: string | null;
  changed_by_name: string | null;
  change_reason: string | null;
  created_at: string;
}

export interface ApiEngagementTeamHistoryList {
  items: ApiEngagementTeamHistory[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiEngagementTeamSummary {
  engagement_id: string;
  total_active: number;
  partner: ApiEngagementTeamMember | null;
  audit_manager: ApiEngagementTeamMember | null;
  by_role: Record<string, ApiEngagementTeamMember[]>;
}

export interface ApiEvidence {
  id: string;
  engagement_id: string;
  project_id: string | null;
  analysis_run_id: string | null;
  root_evidence_id: string | null;
  version_number: number;
  is_current: boolean;
  title: string;
  description: string | null;
  category: string;
  file_name: string;
  content_type: string | null;
  file_size_bytes: number;
  file_hash: string | null;
  status: string;
  metadata: Record<string, unknown>;
  uploaded_by: string | null;
  uploaded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiEvidenceList {
  items: ApiEvidence[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiEvidenceLink {
  id: string;
  evidence_id: string;
  engagement_id: string;
  finding_id: string | null;
  workpaper_id: string | null;
  linked_entity_type: string;
  linked_entity_id: string;
  link_type: string;
  notes: string | null;
  created_by: string | null;
  created_at: string;
}

export interface ApiWorkpaper {
  id: string;
  engagement_id: string;
  project_id: string | null;
  analysis_run_id: string | null;
  root_workpaper_id: string | null;
  version_number: number;
  is_current: boolean;
  reference_code: string;
  title: string;
  description: string | null;
  category: string;
  file_name: string | null;
  content_type: string | null;
  file_size_bytes: number | null;
  file_hash: string | null;
  has_file: boolean;
  status: string;
  metadata: Record<string, unknown>;
  created_by: string | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiWorkpaperList {
  items: ApiWorkpaper[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiFindingLifecycle {
  id: string;
  project_id: string;
  rule_code: string;
  finding_title: string;
  observation: string;
  risk_level: string;
  impact: string;
  recommendation: string;
  affected_count: number;
  status: string;
  management_response: string | null;
  remediation_status: string;
  remediation_notes: string | null;
  remediation_due_date: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiFindingList {
  items: ApiFindingLifecycle[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiAnalysisRun {
  id: string;
  engagement_id: string;
  project_id: string | null;
  module_catalog_id: string | null;
  module_code: string | null;
  run_name: string;
  status: string;
  is_official: boolean;
  job_id: string | null;
  progress_pct: number;
  progress_message: string | null;
  error_message: string | null;
  retry_count: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ApiAnalysisRunList {
  items: ApiAnalysisRun[];
  total: number;
  suggested_names: string[];
}

export interface ApiEngagementHub {
  engagement_id: string;
  financial_year: string;
  status: string;
  enabled_modules: ApiEngagementModule[];
  team_summary: ApiEngagementTeamSummary;
  official_runs: ApiAnalysisRun[];
  latest_runs: ApiAnalysisRun[];
  findings_count: number;
  pending_actions: string[];
}

export interface ApiEngagementReport {
  id: string;
  engagement_id: string;
  report_type: string;
  version_number: number;
  is_official: boolean;
  file_name: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface ApiMessageResponse {
  message: string;
}

export interface ApiInvitePreview {
  email: string;
  full_name: string;
  organization_name: string;
  role: string;
  role_label: string;
  requires_password: boolean;
}

export interface ApiAcceptInviteResponse {
  message: string;
  requires_login: boolean;
  access_token?: string | null;
  refresh_token?: string | null;
  token_type?: string | null;
  expires_in?: number | null;
  user_id?: string | null;
  email?: string | null;
  full_name?: string | null;
  role?: string | null;
  organization_id?: string | null;
  member_role?: string | null;
}

export interface ApiRevenueUploadResponse {
  project_id: string;
  validation: ApiUploadResponse["validation"];
  invoices_imported: number;
  total_taxable: number;
  total_gst: number;
  total_revenue: number;
  message: string;
}

export interface ApiRevenueRunRulesResponse {
  project_id: string;
  total_invoices_analyzed: number;
  total_violations_found: number;
  violations_by_rule: Record<string, number>;
  rule_summary: { rule_code: string; rule_name: string; violation_count: number }[];
  message: string;
}

export interface ApiRevenueRunRiskResponse {
  project_id: string;
  total_invoices_scored: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  message: string;
}

export interface ApiRevenueRiskScore {
  id: string;
  revenue_invoice_id: string;
  total_score: number;
  risk_category: string;
  rule_breakdown: Record<string, number>;
  invoice_no: string;
  invoice_date?: string;
  customer_name: string;
  total_amount: number;
  gst_amount: number;
  payment_status?: string | null;
}

export interface ApiProcurementUploadResponse {
  project_id: string;
  validation: ApiUploadResponse["validation"];
  invoices_imported: number;
  total_taxable: number;
  total_gst: number;
  total_spend: number;
  message: string;
}

export interface ApiProcurementRunRulesResponse {
  project_id: string;
  total_invoices_analyzed: number;
  total_violations_found: number;
  violations_by_rule: Record<string, number>;
  rule_summary: { rule_code: string; rule_name: string; violation_count: number }[];
  message: string;
}

export interface ApiProcurementRunRiskResponse {
  project_id: string;
  total_invoices_scored: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  message: string;
}

export interface ApiProcurementRiskScore {
  id: string;
  procurement_invoice_id: string;
  total_score: number;
  risk_category: string;
  rule_breakdown: Record<string, number>;
  invoice_no: string;
  invoice_date?: string;
  vendor_name: string;
  po_number?: string | null;
  total_amount: number;
  gst_amount: number;
  payment_status?: string | null;
}
