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

/** Maps engagement project types to AI Audit Modules (from the 22-module catalog). */
export const PROJECT_MODULE_MAP: Record<string, ProjectModuleMapping> = {
  journal_testing: {
    primary: ["#1 Journal Entry Testing"],
    supporting: [],
  },
  revenue_testing: {
    primary: ["#2 Revenue Testing"],
    supporting: [
      "#15 Customer Balance Confirmation",
      "#22 Invoice Checking",
      "#13 GST Mismatch Checking",
    ],
  },
  procurement_testing: {
    primary: ["#3 Procurement Testing"],
    supporting: [
      "#7 Purchase Order Matching",
      "#8 Vendor Invoice Validation",
      "#5 Duplicate Payment Checking",
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
