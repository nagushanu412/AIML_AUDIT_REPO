export const MODULE_TITLE = "Procurement Testing";
export const MODULE_DESCRIPTION =
  "Enterprise accounts payable substantive testing — vendor invoice upload, PO matching, duplicate payment detection, GST input validation, and AI-powered exception reporting.";

export const MANDATORY_COLUMNS = [
  "Invoice_No",
  "Invoice_Date",
  "Vendor_Name",
  "Taxable_Amount",
  "GST_Amount",
  "Total_Amount",
] as const;

export const OPTIONAL_COLUMNS = [
  "Vendor_GSTIN",
  "PO_Number",
  "Payment_Status",
  "Reference_No",
] as const;

export const PROCUREMENT_RULES = [
  { code: "PROC_DUPLICATE_PAYMENT", name: "Duplicate Payment", module: "#7" },
  { code: "PROC_MISSING_PO", name: "Missing PO", module: "#5" },
  { code: "PROC_GST_MISMATCH", name: "GST Mismatch", module: "#12" },
  { code: "PROC_HIGH_VALUE", name: "High-Value Invoice", module: "#6" },
  { code: "PROC_ROUND_AMOUNT", name: "Round Amount", module: "#6" },
  { code: "PROC_MISSING_GSTIN", name: "Missing GSTIN", module: "#6" },
  { code: "PROC_CUTOFF", name: "Year-End Cut-Off", module: "#5" },
] as const;

export const ENTERPRISE_MODULES = [
  {
    id: "po-matching",
    number: "#5",
    title: "Purchase Order Matching",
    description: "Three-way match — PO, goods receipt, and vendor invoice alignment.",
  },
  {
    id: "vendor-invoice",
    number: "#6",
    title: "Vendor Invoice Validation",
    description: "Arithmetic accuracy, tax computation, and invoice completeness.",
  },
  {
    id: "duplicate-payment",
    number: "#7",
    title: "Duplicate Payment Checking",
    description: "Detect duplicate vendor payments and overlapping disbursements.",
  },
  {
    id: "gst-itc",
    number: "#12",
    title: "GST Input Tax Credit",
    description: "Validate input GST against vendor invoices and GSTR-2B.",
  },
] as const;

export const WORKFLOW_STEPS = [
  { id: "select", label: "Select Engagement" },
  { id: "upload", label: "Upload Vendor Register" },
  { id: "validate", label: "Validate Data" },
  { id: "analyze", label: "Run AI Analysis" },
  { id: "review", label: "Review Findings" },
  { id: "export", label: "Export Reports" },
] as const;

export const ACCEPTED_FILE_TYPES = [".xlsx"] as const;
