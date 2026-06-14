export const PROJECT_TYPE_LABELS: Record<string, string> = {
  journal_testing: "Journal Testing",
  revenue_testing: "Revenue Testing",
  procurement_testing: "Procurement Testing",
};

export type WorkstreamProjectType = "revenue_testing" | "procurement_testing";

export interface WorkstreamConfig {
  slug: string;
  title: string;
  subtitle: string;
  projectType: WorkstreamProjectType;
  href: string;
  description: string;
}

export const WORKSTREAM_CONFIG: Record<WorkstreamProjectType, WorkstreamConfig> = {
  revenue_testing: {
    slug: "revenue-testing",
    title: "Revenue Testing",
    subtitle: "Sales, receivables, and revenue substantive procedures",
    projectType: "revenue_testing",
    href: "/dashboard/ai-modules/revenue-testing",
    description:
      "Select a revenue testing project for this engagement. Upload and analysis will use AI modules #13 and #20 (and supporting modules) — not the Journal Entry Testing screen.",
  },
  procurement_testing: {
    slug: "procurement-testing",
    title: "Procurement Testing",
    subtitle: "Purchase orders, vendor invoices, and payment controls",
    projectType: "procurement_testing",
    href: "/dashboard/ai-modules/procurement-testing",
    description:
      "Select a procurement testing project for this engagement. Upload and analysis will use AI modules #5, #6, and #7 (and supporting modules) — not the Journal Entry Testing screen.",
  },
};

export interface ProjectModuleMapping {
  primary: string[];
  supporting: string[];
}

/** Maps engagement project types to AI Audit Modules (from the 20-module catalog). */
export const PROJECT_MODULE_MAP: Record<string, ProjectModuleMapping> = {
  journal_testing: {
    primary: ["#1 Journal Entry Testing"],
    supporting: [],
  },
  revenue_testing: {
    primary: ["#20 Invoice Checking", "#13 Customer Balance Confirmation"],
    supporting: [
      "#2 Ledger Scrutiny",
      "#4 GST Mismatch Checking",
      "#18 Supporting Document Matching",
    ],
  },
  procurement_testing: {
    primary: [
      "#5 Purchase Order Matching",
      "#6 Vendor Invoice Validation",
      "#7 Duplicate Payment Checking",
    ],
    supporting: [
      "#12 GST Input Tax Credit Validation",
      "#18 Supporting Document Matching",
      "#20 Invoice Checking",
    ],
  },
};

export function formatProjectType(type: string): string {
  return PROJECT_TYPE_LABELS[type] ?? type.replace(/_/g, " ");
}

export function getModulesForProjectType(type: string): ProjectModuleMapping {
  return (
    PROJECT_MODULE_MAP[type] ?? {
      primary: [],
      supporting: [],
    }
  );
}

export function formatModuleList(mapping: ProjectModuleMapping): string {
  const parts = [...mapping.primary];
  if (mapping.supporting.length) {
    parts.push(`+ ${mapping.supporting.join(", ")}`);
  }
  return parts.join(" · ");
}
