/**
 * MEDHA API Service
 * =================
 *
 * Centralised fetch wrapper for all backend calls.
 *
 * Base URL is read from EXPO_PUBLIC_API_URL (set in .env.local).
 * All authenticated calls supply an Authorization: Bearer <token> header.
 *
 * Environment note:
 *   - Web / iOS Simulator: http://localhost:8000
 *   - Android Emulator:    http://10.0.2.2:8000
 *   - Physical device:     http://<LAN-IP>:8000
 */

import Constants from 'expo-constants';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type {
  CaseSummary,
  SessionSummary,
  CaseResultResponse,
  CheckinSummaryResponse,
  AlertSummaryResponse,
  AlertHandleRequest,
  AlertHandleResponse,
  CaseInsightsResponse,
  CaseRecommendationsResponse,
  SafetyProtocolResponse,
} from '../types/therapist';

export const getStoredToken = async (): Promise<string | null> => {
  if (Platform.OS === 'web') {
    try {
      const val = (await AsyncStorage.getItem('medha_access_token')) || (await AsyncStorage.getItem('MEDHA_JWT'));
      if (val) return val;
    } catch {
      // ignore
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem('medha_access_token') || window.localStorage.getItem('MEDHA_JWT');
    }
    return null;
  }
  try {
    return (await SecureStore.getItemAsync('medha_access_token')) || (await SecureStore.getItemAsync('MEDHA_JWT'));
  } catch {
    return null;
  }
};

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

function resolveBaseUrl(): string {
  const debuggerHost =
    Constants.expoConfig?.hostUri ||
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost ||
    (Constants as any).manifest?.debuggerHost;

  const detectedHost = debuggerHost
    ? debuggerHost.split(':')[0]
    : Platform.OS === 'android'
    ? '10.0.2.2'
    : 'localhost';

  let raw = process.env.EXPO_PUBLIC_API_URL || `http://${detectedHost}:8000`;

  // On Android, 'localhost' refers to the Android device itself.
  // Rewrite localhost / 127.0.0.1 to the dev machine's actual LAN IP or emulator loopback
  if (Platform.OS === 'android') {
    raw = raw.replace(/\b(localhost|127\.0\.0\.1)\b/, detectedHost);
  }

  return raw.replace(/\/+$/, '');
}

export const API_BASE_URL = resolveBaseUrl();
export const API_PREFIX = '/api/v1';

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly detail: string,
    public readonly raw?: unknown,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network unavailable') {
    super(message);
    this.name = 'NetworkError';
  }
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';

interface RequestOptions {
  token?: string | null;
  body?: unknown;
  isMultipart?: boolean;
  signal?: AbortSignal;
}

/**
 * Parse a response, always returning a consistent structure.
 * Non-2xx responses are thrown as ApiError.
 */
async function parseResponse<T>(response: Response): Promise<T> {
  // Try JSON parse regardless of status so we can read error detail
  let json: unknown;
  try {
    json = await response.json();
  } catch {
    json = null;
  }

  if (!response.ok) {
    const detail =
      typeof json === 'object' && json !== null && 'detail' in json
        ? String((json as { detail: unknown }).detail)
        : `HTTP ${response.status}`;
    throw new ApiError(response.status, detail, json);
  }

  return json as T;
}

async function request<T>(
  method: HttpMethod,
  path: string,
  { token, body, isMultipart = false, signal }: RequestOptions = {},
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${path}`;

  const headers: Record<string, string> = {};

  const authToken = token !== undefined ? token : await getStoredToken();
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  // For JSON requests set Content-Type; for multipart let the runtime
  // set the boundary automatically (never set it manually for FormData).
  if (!isMultipart && body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  let fetchBody: BodyInit | undefined;
  if (body instanceof FormData) {
    fetchBody = body;
  } else if (body !== undefined) {
    fetchBody = JSON.stringify(body);
  }

  console.log(`[MEDHA API] ${method} -> ${url}`);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  const combinedSignal = signal || controller.signal;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: fetchBody,
      signal: combinedSignal,
    });
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      throw new NetworkError(`Connection to ${url} timed out. Ensure backend is running with --host 0.0.0.0.`);
    }
    throw new NetworkError(
      err instanceof Error ? err.message : 'Network request failed',
    );
  } finally {
    clearTimeout(timer);
  }

  return parseResponse<T>(response);
}

// ---------------------------------------------------------------------------
// Public API client
// ---------------------------------------------------------------------------

export const api = {
  get<T>(path: string, options?: Omit<RequestOptions, 'body'>): Promise<T> {
    return request<T>('GET', path, options);
  },

  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('POST', path, { ...options, body });
  },

  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PATCH', path, { ...options, body });
  },

  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PUT', path, { ...options, body });
  },

  delete<T>(path: string, options?: Omit<RequestOptions, 'body'>): Promise<T> {
    return request<T>('DELETE', path, options);
  },

  /** Multipart upload — caller builds the FormData. */
  upload<T>(path: string, form: FormData, options?: Omit<RequestOptions, 'body' | 'isMultipart'>): Promise<T> {
    return request<T>('POST', path, { ...options, body: form, isMultipart: true });
  },
};

// ---------------------------------------------------------------------------
// Legacy mock service adapters for unmigrated screens
// ---------------------------------------------------------------------------
// DO NOT use these in new code. They are here only to keep unmigrated screens from crashing.

export const getLegacyToken = getStoredToken;

import { checkinService } from './checkin';
import { journalService } from './journal';
export { checkinService, journalService };

export const chatService = {
  sendMessage: async (sessionId: string, message: string, language?: string) => {
    const t = await getLegacyToken();
    return api.post<{
      session_id: string;
      turn_index: number;
      user_message: string;
      assistant_response: string;
      safety_triggered: boolean;
    }>(`/chat/sessions/${sessionId}/message`, { message, language: language || null }, { token: t });
  },
};

export const sessionService = {
  createSession: async () => {
    const t = await getLegacyToken();
    return api.post<{ id: string; session_identifier: string; timepoint: number; status: string }>('/sessions', undefined, { token: t });
  }
};

export const authService = {
  login: async (email?: string, password?: string) => ({ access_token: 'mock', token_type: 'bearer', user: { role: 'PATIENT' } }),
  logout: () => { },
  getMe: async () => ({}),
};

export const therapistService = {
  getCases: async () => api.get<CaseSummary[]>('/therapist/cases'),
  createPatient: async (data: {
    name: string;
    email: string;
    password: string;
    mobile?: string;
    victim_id?: string;
    case_type?: string;
    status?: string;
  }) => api.post<any>('/therapist/users', data),
  getCaseResults: async (caseId: string) => api.get<CaseResultResponse>(`/therapist/cases/${caseId}/results`),
  getCaseSessions: async (caseId: string) => api.get<SessionSummary[]>(`/therapist/cases/${caseId}/sessions`),
  getCaseCheckins: async (caseId: string) => api.get<CheckinSummaryResponse[]>(`/therapist/cases/${caseId}/checkins`),
  getCaseVoiceRecords: async (caseId: string) => api.get<any[]>(`/therapist/cases/${caseId}/voice-records`),
  getCaseAlerts: async (caseId: string) => api.get<AlertSummaryResponse[]>(`/therapist/cases/${caseId}/alerts`),
  handleCaseAlert: async (caseId: string, alertId: string, data: AlertHandleRequest) =>
    api.patch<AlertHandleResponse>(`/therapist/cases/${caseId}/alerts/${alertId}`, data),
  getCaseInsights: async (caseId: string) => api.get<CaseInsightsResponse>(`/therapist/cases/${caseId}/insights`),
  getCaseRecommendations: async (caseId: string) =>
    api.get<CaseRecommendationsResponse>(`/therapist/cases/${caseId}/recommendations`),
  getCaseSafetyProtocol: async (caseId: string) =>
    api.get<SafetyProtocolResponse>(`/therapist/cases/${caseId}/safety-protocol`),
  acknowledgeAlert: async (caseId: string, alertId: string) =>
    api.patch<AlertHandleResponse>(`/therapist/cases/${caseId}/alerts/${alertId}`, { action: 'ACKNOWLEDGE' }),
  resolveAlert: async (caseId: string, alertId: string, data?: { action_taken?: string }) =>
    api.patch<AlertHandleResponse>(`/therapist/cases/${caseId}/alerts/${alertId}`, { action: 'RESOLVE', ...data }),
  getCaseHistory: async (caseId: string) => api.get<any>(`/therapist/cases/${caseId}/history`),
  updateCaseHistory: async (caseId: string, data: any) => api.put<any>(`/therapist/cases/${caseId}/history`, data),
  getCaseEvents: async (caseId: string, eventType?: string) => {
    const query = eventType ? `?event_type=${encodeURIComponent(eventType)}` : '';
    return api.get<any[]>(`/therapist/cases/${caseId}/events${query}`);
  },
  addCaseEvent: async (caseId: string, data: any) => api.post<any>(`/therapist/cases/${caseId}/events`, data),
  deleteCaseEvent: async (caseId: string, eventId: string) =>
    api.delete<any>(`/therapist/cases/${caseId}/events/${eventId}`),
};

export const voiceService = {
  uploadCheckin: async (
    audioData?: string | Blob,
    timepoint: string = 'current',
    sessionId?: string,
    customFilename?: string
  ) => {
    const token = await getLegacyToken();
    const formData = new FormData();
    formData.append('timepoint', timepoint);
    if (sessionId) formData.append('session_id', sessionId);

    let blob: Blob;
    let fileName = customFilename || 'voice_checkin.wav';

    if (audioData instanceof Blob) {
      blob = audioData;
      if (!customFilename && (audioData as any).name) {
        fileName = (audioData as any).name;
      }
    } else if (typeof audioData === 'string' && audioData.length > 0 && !audioData.includes('dummy')) {
      try {
        if (!customFilename) {
          const parts = audioData.split('/');
          const lastPart = parts[parts.length - 1];
          if (lastPart && (lastPart.endsWith('.m4a') || lastPart.endsWith('.wav') || lastPart.endsWith('.mp3') || lastPart.endsWith('.aac'))) {
            fileName = lastPart;
          }
        }
        const fileRes = await fetch(audioData);
        blob = await fileRes.blob();
      } catch (err) {
        console.warn('Could not read audio uri to blob, using fallback:', err);
        blob = createSilenceWav();
      }
    } else {
      blob = createSilenceWav();
    }

    formData.append('audio_file', blob, fileName);

    return api.upload<any>('/voice/checkin', formData, { token });
  },
};

function createSilenceWav(): Blob {
  const sampleRate = 8000;
  const numSamples = 8000; // 1 second
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);

  // RIFF identifier
  view.setUint32(0, 0x52494646, false);
  view.setUint32(4, 36 + numSamples * 2, true);
  view.setUint32(8, 0x57415645, false); // WAVE
  view.setUint32(12, 0x666d7420, false); // fmt 
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  view.setUint32(36, 0x64617461, false); // data
  view.setUint32(40, numSamples * 2, true);

  return new Blob([buffer], { type: 'audio/wav' });
}

export const apiService = {
  auth: authService,
  session: sessionService,
  chat: chatService,
  checkin: checkinService,
  journal: journalService,
  voice: voiceService,
  therapist: therapistService,
};

export default apiService;
