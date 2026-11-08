/**
 * Authentication Context & Provider.
 *
 * Manages current logged-in user state, session validation with /auth/me,
 * in-memory fallback detection, and secure logout.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { safeStorage } from '../lib/storage';
import { request, setAuthExpiredHandler } from '../lib/api';

export type UserRole = 'admin' | 'student';

export interface AuthUser {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthContextType {
  user: AuthUser | null;
  role: UserRole | 'guest';
  isAuthenticated: boolean;
  isLoading: boolean;
  isMemoryFallback: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const cached = safeStorage.getUser();
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isMemoryFallback, setIsMemoryFallback] = useState<boolean>(() =>
    safeStorage.isMemoryFallback()
  );

  const refreshUser = useCallback(async () => {
    const token = safeStorage.getToken();
    if (!token) {
      setUser(null);
      safeStorage.removeUser();
      setIsLoading(false);
      return;
    }

    try {
      const data = await request<AuthUser | { user: AuthUser }>('/api/v1/auth/me');
      const currentUser = 'user' in data && data.user ? data.user : (data as AuthUser);
      setUser(currentUser);
      safeStorage.setUser(JSON.stringify(currentUser));
    } catch {
      // 401 or invalid session
      setUser(null);
      safeStorage.removeToken();
      safeStorage.removeUser();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check fallback state
    setIsMemoryFallback(safeStorage.isMemoryFallback());

    // Connect 401 handler
    setAuthExpiredHandler(() => {
      setUser(null);
      safeStorage.removeToken();
      safeStorage.removeUser();
    });

    // Validate initial session
    refreshUser();
  }, [refreshUser]);

  const login = useCallback((token: string, newUser: AuthUser) => {
    safeStorage.setToken(token);
    safeStorage.setUser(JSON.stringify(newUser));
    setUser(newUser);
    setIsMemoryFallback(safeStorage.isMemoryFallback());
  }, []);

  const logout = useCallback(async () => {
    try {
      await request('/api/v1/auth/logout', { method: 'POST', idempotent: true });
    } catch {
      // Ignore network errors on logout
    } finally {
      safeStorage.removeToken();
      safeStorage.removeUser();
      setUser(null);
    }
  }, []);

  const value: AuthContextType = {
    user,
    role: user ? user.role : 'guest',
    isAuthenticated: !!user,
    isLoading,
    isMemoryFallback,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
