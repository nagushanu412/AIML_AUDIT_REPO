/** Role-based access — extend when connecting to your identity provider */
export type UserRole =
  | "auditor"
  | "partner"
  | "manager"
  | "admin"
  | "client_viewer";

export type SubscriptionTier = "trial" | "professional" | "enterprise";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  subscription: SubscriptionTier;
  /** Set when 2FA is enabled for the account */
  mfaEnabled: boolean;
  /** Firm / organization identifier for multi-tenant SSO */
  organizationId?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe: boolean;
  /** Reserved for role-based login (e.g. firm portal vs client portal) */
  loginContext?: "firm" | "client";
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface AuthSession {
  user: AuthUser;
  tokens: AuthTokens;
}

export interface AuthResult {
  success: boolean;
  session?: AuthSession;
  error?: string;
  /** Hint for UI when subscription is inactive */
  subscriptionValid?: boolean;
  /** Hint when 2FA challenge is required */
  requiresMfa?: boolean;
}

export interface AuthValidationErrors {
  email?: string;
  password?: string;
  form?: string;
}
