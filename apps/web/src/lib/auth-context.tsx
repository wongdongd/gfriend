'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api, setTokens, clearTokens } from './api';
import type { User } from '@companion/shared';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<User>('/auth/me')
      .then(setUser)
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post<{ access_token: string; refresh_token: string; user_id: string }>(
      '/auth/login',
      { email, password },
    );
    setTokens(res.access_token, res.refresh_token);
    const u = await api.get<User>('/auth/me');
    setUser(u);
  };

  const register = async (email: string, password: string) => {
    const res = await api.post<{ access_token: string; refresh_token: string; user_id: string }>(
      '/auth/register',
      { email, password },
    );
    setTokens(res.access_token, res.refresh_token);
    const u = await api.get<User>('/auth/me');
    setUser(u);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内使用');
  return ctx;
}
