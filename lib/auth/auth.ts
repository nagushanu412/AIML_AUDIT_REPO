import {
  acceptInviteApi,
  forgotPasswordApi,
  loginApi,
  logoutApi,
  previewInviteApi,
  refreshTokenApi,
  registerApi,
} from "@/lib/api";
import { API_BASE_URL } from "@/lib/api/config";
import type { ApiLoginResponse } from "@/lib/api/types";
import type { RegistrationFormData } from "./registrationTypes";
import {
  clearSession,
  getRefreshToken,
  getSession,
  hasAuditorAccess,
  isAccessTokenExpired,
  saveSession,
  updateSessionFromLoginResponse,
  updateSessionTokens,
} from "./session";
import type {
  AuthResult,
  AuthSession,
  AuthValidationErrors,
  LoginCredentials,
} from "./types";
import type { RegistrationResult } from "./registrationTypes";
import { isAuditorPortalRole } from "./roles";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

export function validateLoginForm(
  email: string,
  password: string
): AuthValidationErrors {
  const errors: AuthValidationErrors = {};
  const trimmedEmail = email.trim();

  if (!trimmedEmail) {
    errors.email = "Email is required.";
  } else if (!EMAIL_REGEX.test(trimmedEmail)) {
    errors.email = "Enter a valid work email address.";
  }

  if (!password) {
    errors.password = "Password is required.";
  } else if (password.length < MIN_PASSWORD_LENGTH) {
    errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }

  return errors;
}

function buildSession(
  api: ApiLoginResponse,
  rememberMe = false
): AuthSession {
  return {
    user: {
      id: api.user_id,
      email: api.email,
      name: api.full_name,
      role: api.role as AuthSession["user"]["role"],
      subscription: "professional",
      mfaEnabled: false,
      organizationId: api.organization_id ?? undefined,
      memberRole: api.member_role ?? undefined,
    },
    tokens: {
      accessToken: api.access_token,
      refreshToken: api.refresh_token,
      expiresAt: Date.now() + api.expires_in * 1000,
    },
    rememberMe,
  };
}

function toAuthResult(
  api: ApiLoginResponse,
  rememberMe: boolean
): AuthResult {
  if (!isAuditorPortalRole(api.role)) {
    return {
      success: false,
      error: "Your account does not have auditor portal access.",
    };
  }
  const session = buildSession(api, rememberMe);
  saveSession(session, rememberMe);
  return { success: true, session, subscriptionValid: true, requiresMfa: false };
}

export async function login(credentials: LoginCredentials): Promise<AuthResult> {
  const fieldErrors = validateLoginForm(credentials.email, credentials.password);
  if (fieldErrors.email || fieldErrors.password) {
    return {
      success: false,
      error: fieldErrors.email ?? fieldErrors.password ?? "Invalid input.",
    };
  }

  try {
    const api = await loginApi(
      credentials.email.trim().toLowerCase(),
      credentials.password
    );
    const result = toAuthResult(api, credentials.rememberMe);
    if (result.success && credentials.rememberMe) {
      localStorage.setItem(
        "auditai_remember_email",
        credentials.email.trim().toLowerCase()
      );
    } else {
      localStorage.removeItem("auditai_remember_email");
    }
    return result;
  } catch (err) {
    const message = err instanceof Error ? err.message : "Sign in failed.";
    const hint =
      message === "Failed to fetch" || message.includes("NetworkError")
        ? `Cannot reach the API at ${API_BASE_URL}. Check that the backend is running and CORS is configured.`
        : message;
    return {
      success: false,
      error: hint,
      subscriptionValid: true,
    };
  }
}

export async function register(
  data: RegistrationFormData
): Promise<RegistrationResult & { session?: AuthSession }> {
  try {
    const api = await registerApi({
      email: data.businessEmail.trim().toLowerCase(),
      password: data.password,
      full_name: data.adminFullName.trim(),
      company_name: data.companyName.trim() || undefined,
      phone: data.mobileNumber.trim() || undefined,
    });
    const session = buildSession(api, false);
    saveSession(session, false);
    return { success: true, organizationId: data.companyName, session };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : "Registration failed.",
    };
  }
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    try {
      await logoutApi(refreshToken);
    } catch {
      /* clear local session even if API fails */
    }
  }
  clearSession();
}

export async function forgotPassword(email: string): Promise<string> {
  const res = await forgotPasswordApi(email.trim().toLowerCase());
  return res.message;
}

export async function previewInvite(token: string) {
  return previewInviteApi(token);
}

export async function acceptInvite(
  token: string,
  password?: string
): Promise<AuthResult & { requiresLogin?: boolean }> {
  try {
    const api = await acceptInviteApi({
      token,
      password: password || undefined,
    });

    if (api.requires_login || !api.access_token || !api.refresh_token) {
      return {
        success: true,
        requiresLogin: true,
      };
    }

    const session = buildSession(
      {
        access_token: api.access_token,
        refresh_token: api.refresh_token,
        token_type: api.token_type ?? "bearer",
        expires_in: api.expires_in ?? 3600,
        user_id: api.user_id!,
        email: api.email!,
        full_name: api.full_name!,
        role: api.role!,
        organization_id: api.organization_id ?? null,
        member_role: api.member_role ?? null,
      },
      false
    );
    saveSession(session, false);
    return { success: true, session };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : "Could not accept invitation.",
    };
  }
}

export async function refreshSession(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const api = await refreshTokenApi(refreshToken);
    if (!isAuditorPortalRole(api.role)) {
      clearSession();
      return false;
    }
    updateSessionFromLoginResponse({
      organization_id: api.organization_id,
      member_role: api.member_role,
      full_name: api.full_name,
      email: api.email,
      role: api.role,
    });
    updateSessionTokens({
      accessToken: api.access_token,
      refreshToken: api.refresh_token,
      expiresAt: Date.now() + api.expires_in * 1000,
    });
    return true;
  } catch {
    clearSession();
    return false;
  }
}

export async function ensureValidSession(): Promise<AuthSession | null> {
  const session = getSession();
  if (!session || !hasAuditorAccess(session)) {
    clearSession();
    return null;
  }
  if (!isAccessTokenExpired(session)) {
    return session;
  }
  const refreshed = await refreshSession();
  return refreshed ? getSession() : null;
}

export function getRememberedEmail(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auditai_remember_email");
}
