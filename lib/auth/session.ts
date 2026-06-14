import { AUTH_STORAGE_KEYS } from "./constants";
import { isAuditorPortalRole } from "./roles";
import type { AuthSession } from "./types";

function parseSession(raw: string): AuthSession | null {
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  for (const storage of [sessionStorage, localStorage]) {
    const raw = storage.getItem(AUTH_STORAGE_KEYS.session);
    if (raw) {
      const session = parseSession(raw);
      if (session) return session;
    }
  }
  return null;
}

export function saveSession(session: AuthSession, rememberMe = false): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(AUTH_STORAGE_KEYS.session);
  localStorage.removeItem(AUTH_STORAGE_KEYS.session);
  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem(AUTH_STORAGE_KEYS.session, JSON.stringify(session));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(AUTH_STORAGE_KEYS.session);
  localStorage.removeItem(AUTH_STORAGE_KEYS.session);
}

export function getAccessToken(): string | null {
  return getSession()?.tokens.accessToken ?? null;
}

export function getRefreshToken(): string | null {
  return getSession()?.tokens.refreshToken ?? null;
}

export function isAccessTokenExpired(session: AuthSession): boolean {
  return Date.now() >= session.tokens.expiresAt - 30_000;
}

export function hasAuditorAccess(session: AuthSession | null): boolean {
  if (!session) return false;
  return isAuditorPortalRole(session.user.role);
}

export function updateSessionTokens(
  partial: Pick<AuthSession["tokens"], "accessToken" | "refreshToken" | "expiresAt">
): void {
  const session = getSession();
  if (!session) return;
  session.tokens = { ...session.tokens, ...partial };
  const inLocal = localStorage.getItem(AUTH_STORAGE_KEYS.session) !== null;
  saveSession(session, inLocal);
}

export function getUserInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "AU";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}
