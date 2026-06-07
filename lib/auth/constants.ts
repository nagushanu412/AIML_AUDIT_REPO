import type { LucideIcon } from "lucide-react";
import {
  Building2,
  Copy,
  FileCheck2,
  Landmark,
  Scale,
  Workflow,
} from "lucide-react";

export const PRODUCT_NAME = "AuditAI Platform";
export const TAGLINE = "AI-powered audit automation for modern auditors";

export interface FeatureHighlight {
  id: string;
  label: string;
  icon: LucideIcon;
}

export const FEATURE_HIGHLIGHTS: FeatureHighlight[] = [
  { id: "bank-recon", label: "Bank Reconciliation", icon: Landmark },
  { id: "invoice", label: "Invoice Validation", icon: FileCheck2 },
  { id: "risk", label: "Risk Scoring", icon: Scale },
  { id: "gst-tds", label: "GST/TDS Checks", icon: Building2 },
  { id: "duplicate", label: "Duplicate Payment Detection", icon: Copy },
  {
    id: "workflow",
    label: "Audit Workflow Automation",
    icon: Workflow,
  },
];

/** Demo credentials for local development */
export const DEMO_CREDENTIALS = {
  email: "auditor@demo.auditai.com",
  password: "AuditAI2026!",
} as const;

export const AUTH_STORAGE_KEYS = {
  session: "auditai_session",
  rememberEmail: "auditai_remember_email",
} as const;
