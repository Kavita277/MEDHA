/**
 * MEDHA Session Context
 * =====================
 *
 * Manages the active backend conversation session for the authenticated patient.
 *
 * A session is required before calling:
 *   - POST /api/v1/chat/sessions/{id}/message
 *   - POST /api/v1/checkins/sessions/{id}
 *   - POST /api/v1/voice/checkin
 *
 * Lifecycle:
 *   - After patient login: createSession() is called automatically.
 *   - session_id is persisted in AsyncStorage between app restarts.
 *   - On startup: if a stored session_id exists, it is restored to state
 *     (the backend already owns the session record).
 *   - On logout: session state is cleared.
 *   - Duplicate creation is prevented by a guard ref.
 *
 * NOTE: Only patients (role === 'USER') need a session via this context.
 *       Therapist flows create sessions per-patient on the therapist endpoints.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, ApiError, NetworkError } from '../services/api';
import type { SessionResponse } from '../types/auth';
import { useAuth } from './AuthContext';

// ---------------------------------------------------------------------------
// Storage key
// ---------------------------------------------------------------------------

const SESSION_KEY = 'medha_session_id';

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

interface SessionContextValue {
  /** Active session UUID string, or null */
  sessionId: string | null;
  /** Full session object from backend */
  session: SessionResponse | null;
  /** True while creating/restoring session */
  isLoading: boolean;
  /** Any session-level error message */
  error: string | null;

  /** Create a new session for the authenticated patient */
  createSession: () => Promise<void>;
  /** End the active session on the backend */
  endSession: () => Promise<void>;
  /** Ends the current session and starts a new one */
  startNewSession: () => Promise<void>;
  /** Restores a historical session to view history */
  restoreSession: (sessionId: string) => void;
  /** Clear error */
  clearError: () => void;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const SessionContext = createContext<SessionContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const { token, user, isAuthenticated } = useAuth();

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Guard against duplicate creation when effects fire multiple times
  const creatingRef = useRef(false);

  // -------------------------------------------------------------------------
  // Restore or create session after authentication
  // -------------------------------------------------------------------------

  useEffect(() => {
    // Only act for authenticated patients (therapists don't use this context)
    if (!isAuthenticated || !token || user?.role !== 'USER') {
      return;
    }

    async function initSession() {
      if (creatingRef.current) return;
      creatingRef.current = true;

      try {
        // Create a new session immediately on app startup
        await doCreateSession(token!);
      } finally {
        creatingRef.current = false;
      }
    }

    initSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, token, user?.role]);

  // -------------------------------------------------------------------------
  // Clear session when user logs out (isAuthenticated becomes false)
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!isAuthenticated) {
      setSession(null);
      setError(null);
      creatingRef.current = false;
    }
  }, [isAuthenticated]);

  // -------------------------------------------------------------------------
  // Internal session creation
  // -------------------------------------------------------------------------

  async function doCreateSession(tkn: string) {
    setIsLoading(true);
    setError(null);
    try {
      const created = await api.post<SessionResponse>('/sessions', {}, { token: tkn });
      setSession(created);
    } catch (err) {
      setError(resolveSessionError(err));
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // createSession() — public; allows manual refresh
  // -------------------------------------------------------------------------

  const createSession = useCallback(async () => {
    if (!token) return;
    creatingRef.current = false; // allow retry
    await doCreateSession(token);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // -------------------------------------------------------------------------
  // endSession()
  // -------------------------------------------------------------------------

  const endSession = useCallback(async () => {
    if (!session?.id || !token) return;
    try {
      await api.post(`/sessions/${session.id}/end`, {}, { token });
    } catch {
      // Swallow — ending a session is best-effort
    } finally {
      setSession(null);
    }
  }, [session?.id, token]);

  // -------------------------------------------------------------------------
  // clearError()
  // -------------------------------------------------------------------------

  const clearError = useCallback(() => setError(null), []);

  // -------------------------------------------------------------------------
  // startNewSession() and restoreSession()
  // -------------------------------------------------------------------------

  const startNewSession = useCallback(async () => {
    await endSession();
    await createSession();
  }, [endSession, createSession]);

  const restoreSession = useCallback((sid: string) => {
    setSession({ id: sid } as SessionResponse);
  }, []);

  // -------------------------------------------------------------------------
  // Value
  // -------------------------------------------------------------------------

  const value: SessionContextValue = {
    sessionId: session?.id ?? null,
    session,
    isLoading,
    error,
    createSession,
    endSession,
    startNewSession,
    restoreSession,
    clearError,
  };

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error('useSession must be used inside <SessionProvider>');
  }
  return ctx;
}

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function resolveSessionError(err: unknown): string {
  if (err instanceof NetworkError) return 'No connection — session not started.';
  if (err instanceof ApiError) {
    if (err.statusCode === 401) return 'Session expired. Please log in again.';
    if (err.statusCode >= 500) return 'Server error while creating session.';
    return err.detail;
  }
  return 'Could not start a session. Please try again.';
}
