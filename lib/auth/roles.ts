import type { UserRole } from "./types";

/** Roles allowed to access the auditor dashboard portal */
export const AUDITOR_PORTAL_ROLES: UserRole[] = [
  "auditor",
  "partner",
  "manager",
  "admin",
];

export function isAuditorPortalRole(role: string): role is UserRole {
  return (AUDITOR_PORTAL_ROLES as string[]).includes(role);
}
