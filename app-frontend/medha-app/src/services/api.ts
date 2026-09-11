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

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const RAW_BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
// Strip trailing slash so callers can freely use '/path' prefix
export const API_BASE_URL = RAW_BASE.replace(/\/+$/, '');
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

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
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

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: fetchBody,
      signal,
    });
  } catch (err) {
    // fetch throws on network failure (no connection, DNS failure, etc.)
    throw new NetworkError(
      err instanceof Error ? err.message : 'Network request failed',
    );
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
