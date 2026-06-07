import { DEMO_CREDENTIALS } from "./constants";
import type {
  AuthResult,
  AuthSession,
  AuthValidationErrors,
  LoginCredentials,
} from "./types";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

/** Client-side validation before mock API call */
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

function hasValidationErrors(errors: AuthValidationErrors): boolean {
  return Boolean(errors.email || errors.password || errors.form);
}

/** Simulates network latency — swap with real API / Next.js route handler */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createMockJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify({ ...payload, iat: Date.now() }));
  const signature = btoa("mock-signature");
  return `${header}.${body}.${signature}`;
}

function buildMockSession(email: string): AuthSession {
  const tokens = {
    accessToken: createMockJwt({ sub: "user_demo", email }),
    refreshToken: createMockJwt({ type: "refresh", sub: "user_demo" }),
    expiresAt: Date.now() + 60 * 60 * 1000,
  };

  return {
    user: {
      id: "usr_demo_001",
      email,
      name: "Demo Auditor",
      role: "auditor",
      subscription: "professional",
      mfaEnabled: false,
      organizationId: "org_demo_firm",
    },
    tokens,
  };
}

/**
 * Dummy authentication — replace with:
 * - POST /api/auth/login (JWT issuance)
 * - Subscription gate via billing service
 * - SSO callback handlers (Microsoft / Google)
 * - 2FA challenge when `requiresMfa` is true
 */
export async function mockLogin(
  credentials: LoginCredentials
): Promise<AuthResult> {
  const fieldErrors = validateLoginForm(
    credentials.email,
    credentials.password
  );

  if (hasValidationErrors(fieldErrors)) {
    return {
      success: false,
      error: fieldErrors.email ?? fieldErrors.password ?? "Invalid input.",
    };
  }

  await delay(1200);

  const email = credentials.email.trim().toLowerCase();
  const { password } = credentials;

  if (
    email === DEMO_CREDENTIALS.email.toLowerCase() &&
    password === DEMO_CREDENTIALS.password
  ) {
    const session = buildMockSession(email);

    if (typeof window !== "undefined") {
      const storage = credentials.rememberMe ? localStorage : sessionStorage;
      storage.setItem("auditai_session", JSON.stringify(session));

      if (credentials.rememberMe) {
        localStorage.setItem("auditai_remember_email", email);
      } else {
        localStorage.removeItem("auditai_remember_email");
      }
    }

    return {
      success: true,
      session,
      subscriptionValid: true,
      requiresMfa: false,
    };
  }

  return {
    success: false,
    error: "Invalid email or password. Try the demo credentials shown below.",
    subscriptionValid: true,
  };
}

/** Placeholder for Microsoft Entra ID / Azure AD */
export async function mockMicrosoftSSO(): Promise<AuthResult> {
  await delay(800);
  return {
    success: false,
    error: "Microsoft SSO is not configured yet. Use email sign-in or demo credentials.",
  };
}

/** Placeholder for Google Workspace SSO */
export async function mockGoogleSSO(): Promise<AuthResult> {
  await delay(800);
  return {
    success: false,
    error: "Google SSO is not configured yet. Use email sign-in or demo credentials.",
  };
}

export function getRememberedEmail(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auditai_remember_email");
}
