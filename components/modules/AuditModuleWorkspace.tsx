"use client";

import { useEffect } from "react";
import { fetchModuleWorkspaceConfig, type ModuleCode } from "@/lib/api/modules";

type AuditModuleWorkspaceProps = {
  moduleCode: ModuleCode;
  children: React.ReactNode;
};

/**
 * Generic module workspace host — Phase 3 M2.
 * Validates framework config in the background; renders existing module UI unchanged.
 */
export function AuditModuleWorkspace({ moduleCode, children }: AuditModuleWorkspaceProps) {
  useEffect(() => {
    fetchModuleWorkspaceConfig(moduleCode).catch(() => {
      // Framework bootstrap is best-effort; legacy workspace remains functional.
    });
  }, [moduleCode]);

  return <div data-module={moduleCode}>{children}</div>;
}
