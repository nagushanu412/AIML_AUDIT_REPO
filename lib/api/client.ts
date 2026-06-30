import { AUTH_STORAGE_KEYS } from "@/lib/auth/constants";
import { isAuditorPortalRole } from "@/lib/auth/roles";
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  updateSessionFromLoginResponse,
  updateSessionTokens,
} from "@/lib/auth/session";
import type { AuthSession } from "@/lib/auth/types";
import { API_BASE_URL } from "./config";
import type { ApiLoginResponse } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearSession();
    return false;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearSession();
    return false;
  }

  const api = (await response.json()) as ApiLoginResponse;
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
}

async function tryRefreshToken(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

function getStoredToken(): string | null {
  return getAccessToken();
}

async function parseError(response: Response): Promise<string> {
  let detail = response.statusText;
  try {
    const body = (await response.json()) as { detail?: string | { msg: string }[] };
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      detail = body.detail[0].msg;
    }
  } catch {
    /* ignore */
  }
  return detail || `Request failed (${response.status})`;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { auth?: boolean; _retried?: boolean } = {}
): Promise<T> {
  const { auth = true, headers, _retried = false, ...rest } = options;
  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Content-Type") && !(rest.body instanceof FormData)) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = getStoredToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
  });

  if (response.status === 401 && auth && !_retried) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, _retried: true });
    }
  }

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
  retried = false
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (response.status === 401 && !retried) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiUpload<T>(path, formData, true);
    }
  }

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  return (await response.json()) as T;
}

/** @deprecated Use getAccessToken from lib/auth/session */
export function getSessionFromStorage(): AuthSession | null {
  if (typeof window === "undefined") return null;
  for (const storage of [sessionStorage, localStorage]) {
    const raw = storage.getItem(AUTH_STORAGE_KEYS.session);
    if (!raw) continue;
    try {
      return JSON.parse(raw) as AuthSession;
    } catch {
      continue;
    }
  }
  return null;
}
