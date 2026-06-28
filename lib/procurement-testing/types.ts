export type AnalysisStatus = "idle" | "loading" | "complete" | "error";
export type RiskLevel = "low" | "medium" | "high";
export type SortDirection = "asc" | "desc";
export type SortField = "invoiceDate" | "invoiceNo" | "vendorName" | "totalAmount" | "riskScore";

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

export interface ProcurementValidationSummary {
  mandatoryValid: boolean;
  totalInvoices: number;
  totalTaxable: number;
  totalGst: number;
  totalSpend: number;
}

export interface ProcurementAnalysisSummary {
  totalInvoices: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
}

export interface ProcurementFinding {
  id: string;
  invoiceDate: string;
  invoiceNo: string;
  vendorName: string;
  poNumber: string;
  totalAmount: number;
  gstAmount: number;
  paymentStatus: string;
  riskScore: number;
  riskLevel: RiskLevel;
  aiExplanation: string;
}

export type WorkflowStepId = "select" | "upload" | "validate" | "analyze" | "review" | "export";
