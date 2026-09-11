/**
 * MEDHA Auth Types
 * =================
 *
 * Types mirroring the backend schemas exactly:
 *   POST /api/v1/auth/login  → LoginRequest / TokenResponse
 *   GET  /api/v1/auth/me     → UserResponse
 */

// ---------------------------------------------------------------------------
// Mirrors backend.schemas.user — UserRole, UserStatus, UserResponse
// ---------------------------------------------------------------------------

export type UserRole = 'USER' | 'THERAPIST';
export type UserStatus = 'ACTIVE' | 'SUSPENDED' | 'DEACTIVATED';

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  mobile: string | null;
  role: UserRole;
  status: UserStatus;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

// ---------------------------------------------------------------------------
// Mirrors backend.schemas.auth — LoginRequest / TokenResponse
// ---------------------------------------------------------------------------

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

// ---------------------------------------------------------------------------
// Mirrors backend.schemas.session — SessionCreateRequest / SessionResponse
// ---------------------------------------------------------------------------

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
  state_summary: Record<string, unknown> | null;
}
