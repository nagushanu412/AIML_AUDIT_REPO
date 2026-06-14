"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { ensureValidSession, logout as logoutUser } from "./auth";
import type { AuthSession } from "./types";

interface AuthContextValue {
  session: AuthSession | null;
  isLoading: boolean;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    const valid = await ensureValidSession();
    setSession(valid);
    if (!valid) {
      router.replace("/");
    }
  }, [router]);

  useEffect(() => {
    ensureValidSession()
      .then((valid) => {
        setSession(valid);
        if (!valid) {
          router.replace("/");
        }
      })
      .finally(() => setIsLoading(false));
  }, [router]);

  const logout = useCallback(async () => {
    await logoutUser();
    setSession(null);
    router.replace("/");
  }, [router]);

  const value = useMemo(
    () => ({ session, isLoading, logout, refresh }),
    [session, isLoading, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
