import type { LucideIcon } from "lucide-react";
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
  ShoppingCart,
  UserCheck,
  Users,
  Wallet,
} from "lucide-react";

/** Maps catalog `icon` strings from the API to Lucide components. */
export const MODULE_ICON_MAP: Record<string, LucideIcon> = {
  BookOpen,
  Receipt,
  ShoppingCart,
  FileSpreadsheet,
  Copy,
  Landmark,
  Scale,
  ClipboardCheck,
  Wallet,
  Building2,
  Calculator,
  Banknote,
  FileCheck2,
  Users,
  UserCheck,
  Lock,
  ShieldCheck,
  FileSearch,
  AlertTriangle,
};

export function resolveModuleIcon(name: string): LucideIcon {
  return MODULE_ICON_MAP[name] ?? BookOpen;
}
