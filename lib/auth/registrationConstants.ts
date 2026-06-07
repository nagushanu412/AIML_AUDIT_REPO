import type { LucideIcon } from "lucide-react";
import {
  Bot,
  Building2,
  Cloud,
  ShieldAlert,
  Users,
} from "lucide-react";

export const REGISTRATION_PRODUCT_NAME = "AIML Audit";

export const REGISTRATION_TITLE = "AI-Powered Audit Automation Platform";

export const REGISTRATION_SUBTITLE =
  "Transform audit workflows with Artificial Intelligence, automated risk analysis, intelligent working papers, and real-time audit insights.";

export interface RegistrationBenefit {
  id: string;
  label: string;
  icon: LucideIcon;
}

export const REGISTRATION_BENEFITS: RegistrationBenefit[] = [
  { id: "multi-company", label: "Multi-Company SaaS Platform", icon: Building2 },
  { id: "secure-cloud", label: "Secure Cloud Architecture", icon: Cloud },
  { id: "ai-assistant", label: "AI Audit Assistant", icon: Bot },
  { id: "risk-detection", label: "Automated Risk Detection", icon: ShieldAlert },
  { id: "rbac", label: "Role-Based Access Control", icon: Users },
];

export const TRIAL_BADGES = [
  { id: "trial", label: "14-Day Free Trial" },
  { id: "no-card", label: "No credit card required" },
  { id: "encrypted", label: "Secure & encrypted platform" },
  { id: "multi-tenant", label: "Multi-company SaaS platform" },
] as const;
