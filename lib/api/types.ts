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

export interface ApiLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface ApiMessageResponse {
  message: string;
}
