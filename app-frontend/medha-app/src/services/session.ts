/**
 * Session API Service
 * ===================
 *
 * Client functions for retrieving and managing user sessions.
 */

import { api } from './api';
import type { SessionResponse } from '../types/auth';

/**
 * Retrieves all sessions for the authenticated user's active case.
 */
export async function getSessions(token: string): Promise<SessionResponse[]> {
  return api.get<SessionResponse[]>('/sessions', { token });
}

/**
 * Deletes a session and its associated chat history.
 */
export async function deleteSession(sessionId: string, token: string): Promise<void> {
  return api.delete<void>(`/sessions/${sessionId}`, { token });
}
