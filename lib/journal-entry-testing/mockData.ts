import type {
  AnalysisSummary,
  ClientOption,
  EngagementOption,
  JournalFinding,
  ValidationSummary,
} from "./types";
import { MOCK_FILE_DEFAULT } from "./constants";

export const MOCK_CLIENTS: ClientOption[] = [
  { id: "client-1", name: "Apex Manufacturing Pvt. Ltd." },
  { id: "client-2", name: "Greenfield Logistics LLP" },
  { id: "client-3", name: "Sunrise Retail Chain" },
  { id: "client-4", name: "Pinnacle Finance Co." },
  { id: "client-5", name: "Metro Healthcare Associates" },
];

export const MOCK_ENGAGEMENTS: EngagementOption[] = [
  {
    id: "eng-1",
    clientId: "client-1",
    label: "FY24 Statutory Audit",
    auditPeriod: "01-Apr-2025 to 31-Mar-2026",
    financialYear: "FY 2025-26",
  },
  {
    id: "eng-2",
    clientId: "client-1",
    label: "Q3 Review — Interim",
    auditPeriod: "01-Oct-2025 to 31-Dec-2025",
    financialYear: "FY 2025-26",
  },
  {
    id: "eng-3",
    clientId: "client-2",
    label: "Internal Audit — Q1",
    auditPeriod: "01-Jan-2026 to 31-Mar-2026",
    financialYear: "FY 2025-26",
  },
  {
    id: "eng-4",
    clientId: "client-3",
    label: "FY24 Statutory Audit",
    auditPeriod: "01-Apr-2025 to 31-Mar-2026",
    financialYear: "FY 2025-26",
  },
  {
    id: "eng-5",
    clientId: "client-4",
    label: "Tax & Regulatory Review",
    auditPeriod: "01-Apr-2025 to 31-Mar-2026",
    financialYear: "FY 2025-26",
  },
];

export const MOCK_VALIDATION: ValidationSummary = {
  mandatoryValid: true,
  totalRecords: MOCK_FILE_DEFAULT.recordCount,
  totalDebit: 1_245_875_420,
  totalCredit: 1_245_875_420,
};

export const MOCK_ANALYSIS_SUMMARY: AnalysisSummary = {
  totalEntries: MOCK_FILE_DEFAULT.recordCount,
  highRisk: 15,
  mediumRisk: 48,
  lowRisk: 25369,
};

export const MOCK_FINDINGS: JournalFinding[] = [
  {
    id: "f-1",
    date: "31-Mar-2026",
    voucherNumber: "JV-1001",
    accountName: "Suspense Account",
    debitAmount: 50_00_000,
    creditAmount: 0,
    riskScore: 95,
    riskLevel: "high",
    aiExplanation:
      "Large year-end adjustment impacting suspense account.",
  },
  {
    id: "f-2",
    date: "29-Mar-2026",
    voucherNumber: "JV-0987",
    accountName: "Miscellaneous Expenses",
    debitAmount: 25_00_000,
    creditAmount: 0,
    riskScore: 88,
    riskLevel: "high",
    aiExplanation:
      "Round-amount manual journal posted on weekend; lacks supporting reference.",
  },
  {
    id: "f-3",
    date: "28-Mar-2026",
    voucherNumber: "JV-0972",
    accountName: "Revenue — Other",
    debitAmount: 0,
    creditAmount: 18_75_000,
    riskScore: 82,
    riskLevel: "high",
    aiExplanation:
      "Unusual credit to revenue account near period-end; verify cut-off and approvals.",
  },
  {
    id: "f-4",
    date: "25-Mar-2026",
    voucherNumber: "JV-0941",
    accountName: "Intercompany Payable",
    debitAmount: 12_50_000,
    creditAmount: 0,
    riskScore: 76,
    riskLevel: "medium",
    aiExplanation:
      "Intercompany entry without matching subsidiary confirmation in upload period.",
  },
  {
    id: "f-5",
    date: "22-Mar-2026",
    voucherNumber: "JV-0918",
    accountName: "Inventory Adjustment",
    debitAmount: 8_40_000,
    creditAmount: 0,
    riskScore: 71,
    riskLevel: "medium",
    aiExplanation:
      "Inventory write-off exceeds materiality threshold for Q4 adjustments.",
  },
  {
    id: "f-6",
    date: "18-Mar-2026",
    voucherNumber: "JV-0884",
    accountName: "Professional Fees",
    debitAmount: 5_00_000,
    creditAmount: 0,
    riskScore: 68,
    riskLevel: "medium",
    aiExplanation:
      "Duplicate vendor pattern detected against prior month postings.",
  },
  {
    id: "f-7",
    date: "15-Mar-2026",
    voucherNumber: "JV-0856",
    accountName: "Cash at Bank",
    debitAmount: 0,
    creditAmount: 10_00_000,
    riskScore: 65,
    riskLevel: "medium",
    aiExplanation:
      "Large cash transfer on non-business day; review bank reconciliation support.",
  },
  {
    id: "f-8",
    date: "10-Mar-2026",
    voucherNumber: "JV-0821",
    accountName: "Depreciation Expense",
    debitAmount: 3_75_000,
    creditAmount: 0,
    riskScore: 55,
    riskLevel: "medium",
    aiExplanation:
      "Manual depreciation override; variance from automated run exceeds 12%.",
  },
  {
    id: "f-9",
    date: "05-Mar-2026",
    voucherNumber: "JV-0799",
    accountName: "GST Input Credit",
    debitAmount: 2_20_000,
    creditAmount: 0,
    riskScore: 52,
    riskLevel: "medium",
    aiExplanation:
      "GST account entry posted without tax code reference in optional columns.",
  },
  {
    id: "f-10",
    date: "28-Feb-2026",
    voucherNumber: "JV-0762",
    accountName: "Salaries & Wages",
    debitAmount: 15_00_000,
    creditAmount: 0,
    riskScore: 48,
    riskLevel: "medium",
    aiExplanation:
      "Off-cycle payroll accrual; confirm HR approval and subsequent reversal.",
  },
  {
    id: "f-11",
    date: "20-Feb-2026",
    voucherNumber: "JV-0734",
    accountName: "Rent Expense",
    debitAmount: 4_50_000,
    creditAmount: 0,
    riskScore: 42,
    riskLevel: "low",
    aiExplanation:
      "Recurring rent entry; flagged for completeness of lease schedule linkage.",
  },
  {
    id: "f-12",
    date: "12-Feb-2026",
    voucherNumber: "JV-0701",
    accountName: "Trade Payables",
    debitAmount: 0,
    creditAmount: 6_80_000,
    riskScore: 38,
    riskLevel: "low",
    aiExplanation:
      "Standard supplier payment; low risk but included in stratified sample.",
  },
];
