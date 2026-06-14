export type RiskLevel = "high" | "medium" | "low";

export interface ClientOption {
  id: string;
  name: string;
}

export interface EngagementOption {
  id: string;
  clientId: string;
  label: string;
  auditPeriod: string;
  financialYear: string;
}

export interface UploadedFileInfo {
  name: string;
  sizeBytes: number;
  recordCount: number;
  uploadedAt: Date;
  rawFile?: File;
}

export interface ValidationSummary {
  mandatoryValid: boolean;
  totalRecords: number;
  totalDebit: number;
  totalCredit: number;
}

export interface AnalysisSummary {
  totalEntries: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
}

export interface JournalFinding {
  id: string;
  date: string;
  voucherNumber: string;
  accountName: string;
  debitAmount: number;
  creditAmount: number;
  riskScore: number;
  riskLevel: RiskLevel;
  aiExplanation: string;
}

export type AnalysisStatus = "idle" | "loading" | "complete" | "error";

export type SortField = keyof Pick<
  JournalFinding,
  "date" | "voucherNumber" | "accountName" | "debitAmount" | "creditAmount" | "riskScore" | "riskLevel"
>;

export type SortDirection = "asc" | "desc";
