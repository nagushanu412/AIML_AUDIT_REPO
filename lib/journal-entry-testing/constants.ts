export const MODULE_TITLE = "Journal Entry Testing";

export const MODULE_DESCRIPTION =
  "AI-powered journal entry analysis to identify high-risk transactions, unusual posting patterns, and audit exceptions.";

export const MANDATORY_COLUMNS = [
  "Date",
  "Voucher Number",
  "Account Name",
  "Debit Amount",
  "Credit Amount",
] as const;

export const OPTIONAL_COLUMNS = [
  "Narration",
  "User ID",
  "Cost Center",
  "Department",
  "Reference Number",
] as const;

export const FUTURE_RISK_FACTORS = [
  "Large Value Entries",
  "Year-End Entries",
  "Round Amount Entries",
  "Weekend Entries",
  "Suspense Account Entries",
  "Unusual Posting Patterns",
  "Manual Adjustments",
] as const;

export const COMING_SOON_FEATURES = [
  {
    id: "ml-anomaly",
    title: "ML-Based Anomaly Detection",
    description: "Unsupervised models to surface novel transaction patterns across engagements.",
  },
  {
    id: "llm-assistant",
    title: "LLM Audit Assistant",
    description: "Natural language queries over journal entries and automated narrative drafting.",
  },
  {
    id: "predictive-risk",
    title: "Predictive Risk Analytics",
    description: "Forward-looking risk scores based on historical firm and industry benchmarks.",
  },
  {
    id: "auto-wp",
    title: "Auto Working Paper Generation",
    description: "One-click export of tested samples and conclusions to firm templates.",
  },
  {
    id: "benchmarking",
    title: "Multi-Client Benchmarking",
    description: "Compare journal entry risk profiles across clients and engagement types.",
  },
] as const;

export const ACCEPTED_FILE_TYPES = [".xlsx", ".csv"] as const;

export const MOCK_FILE_DEFAULT = {
  name: "Journal_Entries.xlsx",
  sizeBytes: 2.5 * 1024 * 1024,
  recordCount: 25432,
} as const;
