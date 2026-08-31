import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, apiFetch, type SessionInfo } from "../api/client";

type AuthContextValue = {
  session: SessionInfo | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiFetch<SessionInfo>("/api/auth/session")
      .then((result) => {
        if (!cancelled) setSession(result);
      })
      .catch((err) => {
        if (!cancelled && !(err instanceof ApiError && err.status === 401)) {
          throw err;
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function login(email: string, password: string) {
    const result = await apiFetch<SessionInfo>("/api/auth/login", {
      method: "POST",
      body: { email, password },
    });
    setSession(result);
  }

  async function register(email: string, password: string) {
    const result = await apiFetch<SessionInfo>("/api/auth/register", {
      method: "POST",
      body: { email, password },
    });
    setSession(result);
  }

  async function logout() {
    if (session) {
      await apiFetch("/api/auth/logout", { method: "POST", csrfToken: session.csrf_token });
    }
    setSession(null);
  }

  return (
    <AuthContext.Provider value={{ session, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
