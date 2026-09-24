/**
 * MEDHA Frontend API Service Layer
 * =================================
 * Provides typed, secure client-side communication with the MEDHA backend.
 * Uses native fetch with configurable base URL and strict error sanitization.
 */

export interface SessionCreateRequest {
  case_id?: string | null;
  session_identifier?: string | null;
}

export interface SessionResponse {
  id: string;
  case_id: string;
  victim_id: string;
  session_identifier: string;
  timepoint: number;
  status: string;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
  state_summary?: {
    turn_count: number;
    questions_asked: number;
    current_user_message: string | null;
    latest_assistant_response: string | null;
    text_available: boolean | null;
    voice_available: boolean | null;
  } | null;
}

export interface ChatMessageCreate {
  message: string;
  language?: string | null;
  behaviour_data?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface ChatTurnResult {
  session_id: string;
  turn_index: number;
  user_message: string;
  assistant_response: string;
  timestamp: string;
  safety_triggered: boolean;
}

export interface ChatMessageItem {
  id: string;
  chat_session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessageItem[];
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// In-Memory Token Abstraction
// ---------------------------------------------------------------------------
let inMemoryAccessToken: string | null = null;

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

export function clearAccessToken(): void {
  inMemoryAccessToken = null;
}

// ---------------------------------------------------------------------------
// Base URL Resolution
// ---------------------------------------------------------------------------
export function getApiBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return 'http://localhost:8000';
}

// ---------------------------------------------------------------------------
// Core Request Dispatcher
// ---------------------------------------------------------------------------
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Network connection failed';
    throw new ApiError(`Unable to connect to MEDHA services (${errorMsg})`, 0, 'NETWORK_ERROR');
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && typeof errJson.detail === 'string') {
        errorDetail = errJson.detail;
      }
    } catch {
      // Non-JSON response or parse error
    }
    // Never expose token or headers in thrown error
    throw new ApiError(errorDetail, response.status, `HTTP_${response.status}`);
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

/**
 * Provisions a new conversation session on the backend.
 * Associates the session with the authenticated user's active case.
 */
export async function createSession(
  caseId: string | null = null,
  sessionIdentifier: string | null = null
): Promise<SessionResponse> {
  const token = getAccessToken();
  if (!token) {
    throw new ApiError('Authentication required to create a session.', 401, 'AUTH_REQUIRED');
  }

  return request<SessionResponse>('/api/v1/sessions', {
    method: 'POST',
    body: JSON.stringify({
      case_id: caseId,
      session_identifier: sessionIdentifier,
    }),
  });
}

/**
 * Sends a user message to an active chat session and processes the AI response.
 */
export async function sendMessage(
  sessionId: string,
  message: string,
  options?: {
    language?: string | null;
    behaviour_data?: Record<string, unknown> | null;
    metadata?: Record<string, unknown> | null;
  }
): Promise<ChatTurnResult> {
  const token = getAccessToken();
  if (!token) {
    throw new ApiError('Authentication required to send messages.', 401, 'AUTH_REQUIRED');
  }

  if (!sessionId) {
    throw new ApiError('An active session is required to send messages.', 400, 'SESSION_REQUIRED');
  }

  const payload: ChatMessageCreate = {
    message: message.trim(),
    language: options?.language ?? 'en',
    behaviour_data: options?.behaviour_data ?? null,
    metadata: options?.metadata ?? null,
  };

  return request<ChatTurnResult>(`/api/v1/chat/sessions/${sessionId}/message`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieves the chronologically ordered chat history for an active session.
 */
export async function getHistory(sessionId: string): Promise<ChatHistoryResponse> {
  const token = getAccessToken();
  if (!token) {
    throw new ApiError('Authentication required to retrieve chat history.', 401, 'AUTH_REQUIRED');
  }

  if (!sessionId) {
    throw new ApiError('A session ID is required to retrieve chat history.', 400, 'SESSION_REQUIRED');
  }

  return request<ChatHistoryResponse>(`/api/v1/chat/sessions/${sessionId}/history`, {
    method: 'GET',
  });
}
