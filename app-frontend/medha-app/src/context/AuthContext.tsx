/**
 * MEDHA Auth Context
 * ==================
 *
 * Provides JWT token storage, user identity, and authentication state
 * to the entire application.
 *
 * Token storage strategy:
 *   expo-secure-store is used on native (iOS/Android).
 *   On web, expo-secure-store falls back to localStorage automatically.
 *
 * Startup flow:
 *   1. Read token from secure storage.
 *   2. If found, call GET /api/v1/auth/me to validate.
 *   3. On success → restore authenticated state.
 *   4. On 401 / any failure → clear stored token, stay unauthenticated.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, ApiError, NetworkError } from '../services/api';
import type { LoginRequest, TokenResponse, UserResponse } from '../types/auth';

// ---------------------------------------------------------------------------
// Storage key & Cross-Platform Storage Helpers
// ---------------------------------------------------------------------------

const TOKEN_KEY = 'medha_access_token';

async function storeToken(token: string): Promise<void> {
  if (Platform.OS === 'web') {
    try {
      await AsyncStorage.setItem(TOKEN_KEY, token);
    } catch {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(TOKEN_KEY, token);
      }
    }
  } else {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  }
}

async function getStoredToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    try {
      const val = await AsyncStorage.getItem(TOKEN_KEY);
      if (val) return val;
    } catch {
      // fallback to localStorage
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(TOKEN_KEY);
    }
    return null;
  } else {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  }
}

async function removeStoredToken(): Promise<void> {
  if (Platform.OS === 'web') {
    try {
      await AsyncStorage.removeItem(TOKEN_KEY);
    } catch {
      // fallback
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } else {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
  }
}

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

interface AuthContextValue {
  /** The raw JWT string, or null when unauthenticated */
  token: string | null;
  /** Authenticated user profile */
  user: UserResponse | null;
  /** True while the app is restoring auth state on startup */
  isLoading: boolean;
  /** True once the token has been validated against /auth/me */
  isAuthenticated: boolean;
  /** Any auth-level error message */
  error: string | null;

  /** Authenticate with email + password → persists token, sets user */
  login: (credentials: LoginRequest) => Promise<void>;
  /** Clear all auth state + storage */
  logout: () => Promise<void>;
  /** Clear the current error */
  clearError: () => void;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);   // true until restoration completes
  const [error, setError] = useState<string | null>(null);

  // Prevent double-restoration during StrictMode double-mount
  const restoredRef = useRef(false);

  // -------------------------------------------------------------------------
  // Restore persisted session on startup
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;

    async function restore() {
      try {
        const stored = await getStoredToken();
        if (!stored) {
          return; // No stored token → stay unauthenticated
        }

        // Validate token by fetching user profile
        try {
          const me = await api.get<UserResponse>('/auth/me', { token: stored });
          setToken(stored);
          setUser(me);
        } catch (err) {
          // Token invalid or expired — clear it silently
          await removeStoredToken();
          // Stay unauthenticated
        }
      } catch {
        // Storage read failure — treat as unauthenticated
      } finally {
        setIsLoading(false);
      }
    }

    restore();
  }, []);

  // -------------------------------------------------------------------------
  // login()
  // -------------------------------------------------------------------------

  const login = useCallback(async (credentials: LoginRequest) => {
    setError(null);
    try {
      const response = await api.post<TokenResponse>('/auth/login', credentials);
      await storeToken(response.access_token);
      setToken(response.access_token);
      setUser(response.user);
    } catch (err) {
      const message = resolveErrorMessage(err);
      setError(message);
      throw err; // re-throw so screens can react
    }
  }, []);

  // -------------------------------------------------------------------------
  // logout()
  // -------------------------------------------------------------------------

  const logout = useCallback(async () => {
    setToken(null);
    setUser(null);
    setError(null);
    try {
      await removeStoredToken();
    } catch {
      // Ignore storage errors during logout
    }
  }, []);

  // -------------------------------------------------------------------------
  // clearError()
  // -------------------------------------------------------------------------

  const clearError = useCallback(() => setError(null), []);

  // -------------------------------------------------------------------------
  // Value
  // -------------------------------------------------------------------------

  const value: AuthContextValue = {
    token,
    user,
    isLoading,
    isAuthenticated: token !== null && user !== null,
    error,
    login,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function resolveErrorMessage(err: unknown): string {
  if (err instanceof NetworkError) {
    return 'Could not reach the server. Please check your connection.';
  }
  if (err instanceof ApiError) {
    if (err.statusCode === 401) return 'Incorrect email or password.';
    if (err.statusCode === 403) return 'Your account is not authorised to log in.';
    if (err.statusCode >= 500) return 'The server encountered an error. Please try again.';
    return err.detail;
  }
  return 'Something went wrong. Please try again.';
}
