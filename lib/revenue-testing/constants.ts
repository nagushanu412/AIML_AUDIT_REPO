export const MODULE_TITLE = "Revenue Testing";
export const MODULE_DESCRIPTION =
  "Enterprise revenue substantive testing — sales register upload, invoice validation, GST checks, customer balance review, and AI-powered exception reporting for statutory audit engagements.";

export const MANDATORY_COLUMNS = [
  "Invoice_No",
  "Invoice_Date",
  "Customer_Name",
  "Taxable_Amount",
  "GST_Amount",
  "Total_Amount",
] as const;

export const OPTIONAL_COLUMNS = [
  "Customer_GSTIN",
  "Payment_Status",
  "Reference_No",
] as const;

export const REVENUE_RULES = [
  { code: "REV_DUPLICATE_INVOICE", name: "Duplicate Invoice", module: "#20" },
  { code: "REV_CUTOFF", name: "Year-End Cut-Off", module: "#20" },
  { code: "REV_GST_MISMATCH", name: "GST Mismatch", module: "#4" },
  { code: "REV_ROUND_AMOUNT", name: "Round Amount", module: "#20" },
  { code: "REV_HIGH_VALUE", name: "High-Value Invoice", module: "#13" },
  { code: "REV_MISSING_GSTIN", name: "Missing GSTIN", module: "#20" },
  { code: "REV_UNPAID_LARGE", name: "Large Unpaid", module: "#13" },
] as const;

export const ENTERPRISE_MODULES = [
  {
    id: "invoice-checking",
    number: "#20",
    title: "Invoice Checking",
    description: "Arithmetic accuracy, tax computation, and invoice completeness validation.",
  },
  {
    id: "customer-balance",
    number: "#13",
    title: "Customer Balance Confirmation",
    description: "Receivables review, unpaid balances, and confirmation readiness.",
  },
  {
    id: "gst-mismatch",
    number: "#4",
    title: "GST Mismatch Checking",
    description: "Cross-check GST amounts against standard rates and taxable values.",
  },
  {
    id: "ledger-scrutiny",
    number: "#2",
    title: "Ledger Scrutiny",
    description: "Supporting revenue GL account variance and trend analysis.",
  },
] as const;

export const WORKFLOW_STEPS = [
  { id: "select", label: "Select Engagement" },
  { id: "upload", label: "Upload Sales Register" },
  { id: "validate", label: "Validate Data" },
  { id: "analyze", label: "Run AI Analysis" },
  { id: "review", label: "Review Findings" },
  { id: "export", label: "Export Reports" },
] as const;

export const ACCEPTED_FILE_TYPES = [".xlsx"] as const;
