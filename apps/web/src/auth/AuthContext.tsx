import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getCurrentUser, login as loginRequest } from "../api/mangaApi";
import type { AuthUser } from "../api/types";

const TOKEN_KEY = "web_manga_auth_token";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    let active = true;
    if (!token) {
      setUser(null);
      setLoading(false);
      return () => {
        active = false;
      };
    }

    setLoading(true);
    getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (active) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      login: async (username: string, password: string) => {
        const response = await loginRequest(username, password);
        localStorage.setItem(TOKEN_KEY, response.access_token);
        setToken(response.access_token);
        setUser(response.user);
        return response.user;
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      },
    }),
    [loading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
