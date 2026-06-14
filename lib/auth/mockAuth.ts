import type { AuthResult } from "./types";

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Placeholder for Microsoft Entra ID / Azure AD */
export async function mockMicrosoftSSO(): Promise<AuthResult> {
  await delay(800);
  return {
    success: false,
    error: "Microsoft SSO is not configured yet. Use email sign-in.",
  };
}

/** Placeholder for Google Workspace SSO */
export async function mockGoogleSSO(): Promise<AuthResult> {
  await delay(800);
  return {
    success: false,
    error: "Google SSO is not configured yet. Use email sign-in.",
  };
}
