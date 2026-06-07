import {
  AlertTriangle,
  Banknote,
  BookOpen,
  Building2,
  Calculator,
  ClipboardCheck,
  Copy,
  FileCheck2,
  FileSearch,
  FileSpreadsheet,
  Landmark,
  Lock,
  Receipt,
  Scale,
  ShieldCheck,
  UserCheck,
  Users,
  Wallet,
} from "lucide-react";
import type { AuditModule } from "./types";

export const AUDIT_MODULES: AuditModule[] = [
  {
    id: "journal-entry-testing",
    name: "Journal Entry Testing",
    description:
      "AI-assisted analysis of journal entries for anomalies, unusual patterns, and manual adjustments requiring review.",
    status: "active",
    slug: "journal-entry-testing",
    icon: BookOpen,
    category: "General Ledger",
  },
  {
    id: "ledger-scrutiny",
    name: "Ledger Scrutiny",
    description:
      "Automated scrutiny of general ledger accounts with variance analysis, trend detection, and account-level risk scoring.",
    status: "active",
    slug: "ledger-scrutiny",
    icon: FileSpreadsheet,
    category: "General Ledger",
  },
  {
    id: "duplicate-payment-checking",
    name: "Duplicate Payment Checking",
    description:
      "Detect duplicate vendor payments, repeated invoice references, and overlapping disbursements across transactions.",
    status: "active",
    slug: "duplicate-payment-checking",
    icon: Copy,
    category: "Accounts Payable",
  },
  {
    id: "bank-reconciliation",
    name: "Bank Reconciliation",
    description:
      "Match bank statements with book records using AI-powered reconciliation and exception highlighting.",
    status: "coming_soon",
    slug: "bank-reconciliation",
    icon: Landmark,
    category: "Cash & Bank",
  },
  {
    id: "gst-mismatch-checking",
    name: "GST Mismatch Checking",
    description:
      "Identify GST return discrepancies between books, invoices, and filed returns with automated variance reports.",
    status: "coming_soon",
    slug: "gst-mismatch-checking",
    icon: Scale,
    category: "Indirect Tax",
  },
  {
    id: "purchase-order-matching",
    name: "Purchase Order Matching",
    description:
      "Three-way match between purchase orders, goods receipt notes, and vendor invoices for procurement controls.",
    status: "coming_soon",
    slug: "purchase-order-matching",
    icon: ClipboardCheck,
    category: "Procurement",
  },
  {
    id: "vendor-invoice-validation",
    name: "Vendor Invoice Validation",
    description:
      "Validate vendor invoices against contracts, tax rules, approval limits, and master data integrity.",
    status: "coming_soon",
    slug: "vendor-invoice-validation",
    icon: Receipt,
    category: "Accounts Payable",
  },
  {
    id: "expense-claim-verification",
    name: "Expense Claim Verification",
    description:
      "Review employee expense claims for policy compliance, duplicate submissions, and supporting documentation.",
    status: "coming_soon",
    slug: "expense-claim-verification",
    icon: Wallet,
    category: "Expenses",
  },
  {
    id: "fixed-asset-verification",
    name: "Fixed Asset Verification",
    description:
      "Reconcile fixed asset registers with physical verification records and capitalization policies.",
    status: "coming_soon",
    slug: "fixed-asset-verification",
    icon: Building2,
    category: "Fixed Assets",
  },
  {
    id: "depreciation-recalculation",
    name: "Depreciation Recalculation",
    description:
      "Recalculate depreciation under applicable accounting standards and flag variances from recorded amounts.",
    status: "coming_soon",
    slug: "depreciation-recalculation",
    icon: Calculator,
    category: "Fixed Assets",
  },
  {
    id: "tds-deduction-checking",
    name: "TDS Deduction Checking",
    description:
      "Verify TDS deductions, applicable rates, and challan remittances against statutory requirements.",
    status: "coming_soon",
    slug: "tds-deduction-checking",
    icon: Banknote,
    category: "Direct Tax",
  },
  {
    id: "gst-itc-validation",
    name: "GST Input Tax Credit Validation",
    description:
      "Validate ITC eligibility, invoice matching, and reversal requirements under GST regulations.",
    status: "coming_soon",
    slug: "gst-itc-validation",
    icon: FileCheck2,
    category: "Indirect Tax",
  },
  {
    id: "customer-balance-confirmation",
    name: "Customer Balance Confirmation Tracking",
    description:
      "Track customer balance confirmation requests, responses, and follow-ups for receivables audit procedures.",
    status: "coming_soon",
    slug: "customer-balance-confirmation",
    icon: Users,
    category: "Accounts Receivable",
  },
  {
    id: "payroll-audit-checking",
    name: "Payroll Audit Checking",
    description:
      "Audit payroll computations, statutory deductions, and headcount reconciliations for accuracy and compliance.",
    status: "coming_soon",
    slug: "payroll-audit-checking",
    icon: UserCheck,
    category: "Payroll",
  },
  {
    id: "user-access-review",
    name: "User Access Review",
    description:
      "Review user access rights and privileged accounts for IT general controls and regulatory compliance.",
    status: "coming_soon",
    slug: "user-access-review",
    icon: Lock,
    category: "IT Controls",
  },
  {
    id: "segregation-of-duties",
    name: "Segregation of Duties Checking",
    description:
      "Identify conflicts in user roles and incompatible duty assignments across ERP and financial systems.",
    status: "coming_soon",
    slug: "segregation-of-duties",
    icon: ShieldCheck,
    category: "IT Controls",
  },
  {
    id: "compliance-checklist",
    name: "Compliance Checklist Verification",
    description:
      "Verify completion of regulatory, engagement, and firm compliance checklists with audit trail tracking.",
    status: "coming_soon",
    slug: "compliance-checklist",
    icon: ClipboardCheck,
    category: "Compliance",
  },
  {
    id: "supporting-document-matching",
    name: "Supporting Document Matching",
    description:
      "Match transactions with supporting vouchers, invoices, approvals, and underlying documentation.",
    status: "coming_soon",
    slug: "supporting-document-matching",
    icon: FileSearch,
    category: "Documentation",
  },
  {
    id: "exception-report-preparation",
    name: "Exception Report Preparation",
    description:
      "Auto-generate exception reports from audit test results, findings, and unresolved review items.",
    status: "coming_soon",
    slug: "exception-report-preparation",
    icon: AlertTriangle,
    category: "Reporting",
  },
  {
    id: "invoice-checking",
    name: "Invoice Checking",
    description:
      "Validate sales and purchase invoices for arithmetic accuracy, tax computation, and completeness.",
    status: "coming_soon",
    slug: "invoice-checking",
    icon: Receipt,
    category: "Revenue & AP",
  },
];
