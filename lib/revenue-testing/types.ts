export type AnalysisStatus = "idle" | "loading" | "complete" | "error";
export type RiskLevel = "low" | "medium" | "high";
export type SortDirection = "asc" | "desc";
export type SortField = "invoiceDate" | "invoiceNo" | "customerName" | "totalAmount" | "riskScore";

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

export interface RevenueValidationSummary {
  mandatoryValid: boolean;
  totalInvoices: number;
  totalTaxable: number;
  totalGst: number;
  totalRevenue: number;
}

export interface RevenueAnalysisSummary {
  totalInvoices: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
}

export interface RevenueFinding {
  id: string;
  invoiceDate: string;
  invoiceNo: string;
  customerName: string;
  totalAmount: number;
  gstAmount: number;
  paymentStatus: string;
  riskScore: number;
  riskLevel: RiskLevel;
  aiExplanation: string;
}

export type WorkflowStepId = "select" | "upload" | "validate" | "analyze" | "review" | "export";
